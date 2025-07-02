import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime

from livekit.agents import AgentSession, MetricsCollectedEvent
from livekit.agents.metrics.base import AgentMetrics, STTMetrics, EOUMetrics, LLMMetrics, TTSMetrics

logger = logging.getLogger(__name__)


@dataclass
class TurnLatencyMetrics:
    """Latency metrics for a single conversational turn."""
    
    turn_id: str
    start_timestamp: float
    
    # STT Metrics
    stt_duration: Optional[float] = None
    stt_audio_duration: Optional[float] = None
    stt_streamed: Optional[bool] = None
    
    # EOU Metrics  
    eou_end_of_utterance_delay: Optional[float] = None
    eou_transcription_delay: Optional[float] = None
    eou_callback_delay: Optional[float] = None
    
    # LLM Metrics
    llm_ttft: Optional[float] = None  # Time to First Token
    llm_total_duration: Optional[float] = None
    llm_tokens_per_second: Optional[float] = None
    llm_cancelled: Optional[bool] = None
    
    # TTS Metrics
    tts_ttfb: Optional[float] = None  # Time to First Byte
    tts_total_duration: Optional[float] = None
    tts_audio_duration: Optional[float] = None
    tts_cancelled: Optional[bool] = None
    
    # Interruption tracking
    was_interrupted: bool = False
    interruption_stage: Optional[str] = None  # 'llm', 'tts', 'completed'
    
    # Calculated Total Latencies
    total_response_latency: Optional[float] = None
    speech_id: Optional[str] = None
    
    def calculate_total_latency(self) -> Optional[float]:
        """Calculate total conversation latency as per LiveKit docs:
        total_latency = eou.end_of_utterance_delay + llm.ttft + tts.ttfb
        
        For interrupted turns, calculate partial latency up to interruption point.
        """
        if self.was_interrupted:
            # Calculate partial latency based on what completed before interruption
            partial_latency = 0.0
            
            if self.eou_end_of_utterance_delay:
                partial_latency += self.eou_end_of_utterance_delay
            
            if self.llm_ttft and not self.llm_cancelled:
                partial_latency += self.llm_ttft
            
            if self.tts_ttfb and not self.tts_cancelled:
                partial_latency += self.tts_ttfb
            
            self.total_response_latency = partial_latency if partial_latency > 0 else None
            return self.total_response_latency
        
        # Normal case: all components completed
        if all([self.eou_end_of_utterance_delay, self.llm_ttft, self.tts_ttfb]):
            self.total_response_latency = (
                self.eou_end_of_utterance_delay + 
                self.llm_ttft + 
                self.tts_ttfb
            )
            return self.total_response_latency
        return None
    
    def mark_interrupted(self, stage: str):
        """Mark this turn as interrupted at a specific stage."""
        self.was_interrupted = True
        self.interruption_stage = stage
        logger.debug(f"Turn {self.turn_id} interrupted during {stage}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/export."""
        return {
            "turn_id": self.turn_id,
            "start_timestamp": self.start_timestamp,
            "was_interrupted": self.was_interrupted,
            "interruption_stage": self.interruption_stage,
            "stt": {
                "duration": self.stt_duration,
                "audio_duration": self.stt_audio_duration,
                "streamed": self.stt_streamed
            },
            "eou": {
                "end_of_utterance_delay": self.eou_end_of_utterance_delay,
                "transcription_delay": self.eou_transcription_delay,
                "callback_delay": self.eou_callback_delay
            },
            "llm": {
                "ttft": self.llm_ttft,
                "total_duration": self.llm_total_duration,
                "tokens_per_second": self.llm_tokens_per_second,
                "cancelled": self.llm_cancelled
            },
            "tts": {
                "ttfb": self.tts_ttfb,
                "total_duration": self.tts_total_duration,
                "audio_duration": self.tts_audio_duration,
                "cancelled": self.tts_cancelled
            },
            "totals": {
                "response_latency": self.total_response_latency,
                "calculated_at": datetime.now().isoformat()
            }
        }


class TurnLatencyTracker:
    """Tracks latency metrics for each conversational turn."""
    
    def __init__(self):
        self.current_turn: Optional[TurnLatencyMetrics] = None
        self.completed_turns: List[TurnLatencyMetrics] = []
        self.turn_counter = 0
        self.last_speech_id: Optional[str] = None
        
    def start_new_turn(self) -> str:
        """Start tracking a new conversational turn."""
        self.turn_counter += 1
        turn_id = f"turn_{self.turn_counter}_{int(time.time())}"
        
        # Complete previous turn if exists (likely interrupted)
        if self.current_turn:
            self.complete_current_turn(reason="new_turn_started")
        
        self.current_turn = TurnLatencyMetrics(
            turn_id=turn_id,
            start_timestamp=time.time()
        )
        
        logger.debug(f"🔄 Started tracking turn: {turn_id}")
        return turn_id
    
    def update_stt_metrics(self, stt_metrics: STTMetrics):
        """Update current turn with STT metrics."""
        if not self.current_turn:
            return
            
        self.current_turn.stt_duration = stt_metrics.duration
        self.current_turn.stt_audio_duration = stt_metrics.audio_duration
        self.current_turn.stt_streamed = stt_metrics.streamed
        
        logger.debug(f"📝 STT metrics for {self.current_turn.turn_id}: "
                    f"duration={stt_metrics.duration:.3f}s, "
                    f"audio_duration={stt_metrics.audio_duration:.3f}s")
    
    def update_eou_metrics(self, eou_metrics: EOUMetrics):
        """Update current turn with EOU metrics."""
        if not self.current_turn:
            return
            
        self.current_turn.eou_end_of_utterance_delay = eou_metrics.end_of_utterance_delay
        self.current_turn.eou_transcription_delay = eou_metrics.transcription_delay
        self.current_turn.eou_callback_delay = eou_metrics.on_user_turn_completed_delay
        self.current_turn.speech_id = eou_metrics.speech_id
        
        logger.debug(f"🎯 EOU metrics for {self.current_turn.turn_id}: "
                    f"eou_delay={eou_metrics.end_of_utterance_delay:.3f}s, "
                    f"transcription_delay={eou_metrics.transcription_delay:.3f}s")
    
    def update_llm_metrics(self, llm_metrics: LLMMetrics):
        """Update current turn with LLM metrics."""
        if not self.current_turn:
            return
            
        self.current_turn.llm_ttft = llm_metrics.ttft
        self.current_turn.llm_total_duration = llm_metrics.duration
        self.current_turn.llm_tokens_per_second = llm_metrics.tokens_per_second
        self.current_turn.llm_cancelled = llm_metrics.cancelled
        
        if llm_metrics.cancelled:
            self.current_turn.mark_interrupted("llm")
            logger.debug(f"🧠 LLM interrupted for {self.current_turn.turn_id}: "
                        f"ttft={llm_metrics.ttft:.3f}s before cancellation")
        else:
            logger.debug(f"🧠 LLM metrics for {self.current_turn.turn_id}: "
                        f"ttft={llm_metrics.ttft:.3f}s, "
                        f"duration={llm_metrics.duration:.3f}s")
    
    def update_tts_metrics(self, tts_metrics: TTSMetrics):
        """Update current turn with TTS metrics."""
        if not self.current_turn:
            return
            
        self.current_turn.tts_ttfb = tts_metrics.ttfb
        self.current_turn.tts_total_duration = tts_metrics.duration
        self.current_turn.tts_audio_duration = tts_metrics.audio_duration
        self.current_turn.tts_cancelled = tts_metrics.cancelled
        
        if tts_metrics.cancelled:
            self.current_turn.mark_interrupted("tts")
            logger.debug(f"🎤 TTS interrupted for {self.current_turn.turn_id}: "
                        f"ttfb={tts_metrics.ttfb:.3f}s before cancellation")
        else:
            logger.debug(f"🎤 TTS metrics for {self.current_turn.turn_id}: "
                        f"ttfb={tts_metrics.ttfb:.3f}s, "
                        f"duration={tts_metrics.duration:.3f}s")
        
        # Complete turn when TTS starts or gets cancelled
        self.complete_current_turn(reason="tts_completed_or_cancelled")
    
    def handle_interruption_from_new_stt(self):
        """Handle when a new STT event indicates user interrupted ongoing turn."""
        if self.current_turn:
            # Determine what stage was interrupted
            if self.current_turn.tts_ttfb is not None:
                # TTS had started, so user interrupted during TTS playback
                self.current_turn.mark_interrupted("tts")
            elif self.current_turn.llm_ttft is not None:
                # LLM had started, so user interrupted during LLM generation
                self.current_turn.mark_interrupted("llm")
            else:
                # Very early interruption
                self.current_turn.mark_interrupted("early")
            
            self.complete_current_turn(reason="user_interruption")
    
    def complete_current_turn(self, reason: str = "normal"):
        """Complete the current turn and calculate final metrics."""
        if not self.current_turn:
            return
            
        # Calculate total latency (handles interruptions)
        total_latency = self.current_turn.calculate_total_latency()
        
        # Log comprehensive turn summary
        self.log_turn_summary(self.current_turn, reason)
        
        # Store completed turn
        self.completed_turns.append(self.current_turn)
        self.current_turn = None
        
        if total_latency:
            status = "interrupted" if self.completed_turns[-1].was_interrupted else "completed"
            logger.info(f"✅ Turn {status} with {'partial' if self.completed_turns[-1].was_interrupted else 'total'} latency: {total_latency:.3f}s")
        else:
            logger.info(f"✅ Turn completed (partial metrics, reason: {reason})")
    
    def log_turn_summary(self, turn: TurnLatencyMetrics, completion_reason: str = "normal"):
        """Log detailed turn latency summary."""
        interrupt_status = " [INTERRUPTED]" if turn.was_interrupted else ""
        logger.debug(f"📊 TURN LATENCY SUMMARY - {turn.turn_id}{interrupt_status}")
        
        if turn.was_interrupted:
            logger.debug(f"   ⚠️  Interruption during: {turn.interruption_stage}")
        
        logger.debug(f"   📝 STT Duration: {turn.stt_duration:.3f}s" if turn.stt_duration else "   📝 STT Duration: N/A")
        logger.debug(f"   🎯 EOU Detection Delay: {turn.eou_end_of_utterance_delay:.3f}s" if turn.eou_end_of_utterance_delay else "   🎯 EOU Detection Delay: N/A")
        
        llm_status = " (cancelled)" if turn.llm_cancelled else ""
        logger.debug(f"   🧠 LLM TTFT: {turn.llm_ttft:.3f}s{llm_status}" if turn.llm_ttft else "   🧠 LLM TTFT: N/A")
        
        tts_status = " (cancelled)" if turn.tts_cancelled else ""
        logger.debug(f"   🎤 TTS TTFB: {turn.tts_ttfb:.3f}s{tts_status}" if turn.tts_ttfb else "   🎤 TTS TTFB: N/A")
        
        latency_type = "PARTIAL" if turn.was_interrupted else "TOTAL"
        logger.debug(f"   ⏱️  {latency_type} RESPONSE LATENCY: {turn.total_response_latency:.3f}s" if turn.total_response_latency else f"   ⏱️  {latency_type} RESPONSE LATENCY: Incomplete")
        logger.debug(f"   ────────────────────────────────")
    
    def get_turn_metrics(self, turn_id: str) -> Optional[TurnLatencyMetrics]:
        """Get metrics for a specific turn."""
        for turn in self.completed_turns:
            if turn.turn_id == turn_id:
                return turn
        return None
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get aggregated statistics for the entire session."""
        if not self.completed_turns:
            return {"total_turns": 0, "message": "No completed turns"}
        
        # Separate completed vs interrupted turns
        completed_turns = [t for t in self.completed_turns if not t.was_interrupted and t.total_response_latency is not None]
        interrupted_turns = [t for t in self.completed_turns if t.was_interrupted]
        
        stats = {
            "total_turns": len(self.completed_turns),
            "completed_turns": len(completed_turns),
            "interrupted_turns": len(interrupted_turns),
            "interruption_rate": len(interrupted_turns) / len(self.completed_turns) if self.completed_turns else 0,
        }
        
        # Add interruption breakdown
        if interrupted_turns:
            interruption_stages = {}
            for turn in interrupted_turns:
                stage = turn.interruption_stage or "unknown"
                interruption_stages[stage] = interruption_stages.get(stage, 0) + 1
            stats["interruption_breakdown"] = interruption_stages
        
        # Calculate averages for completed turns only
        if completed_turns:
            stats.update({
                "average_response_latency": sum(t.total_response_latency for t in completed_turns) / len(completed_turns),
                "average_stt_duration": sum(t.stt_duration for t in completed_turns if t.stt_duration) / len([t for t in completed_turns if t.stt_duration]),
                "average_eou_delay": sum(t.eou_end_of_utterance_delay for t in completed_turns if t.eou_end_of_utterance_delay) / len([t for t in completed_turns if t.eou_end_of_utterance_delay]),
                "average_llm_ttft": sum(t.llm_ttft for t in completed_turns if t.llm_ttft and not t.llm_cancelled) / len([t for t in completed_turns if t.llm_ttft and not t.llm_cancelled]),
                "average_tts_ttfb": sum(t.tts_ttfb for t in completed_turns if t.tts_ttfb and not t.tts_cancelled) / len([t for t in completed_turns if t.tts_ttfb and not t.tts_cancelled]),
                "min_response_latency": min(t.total_response_latency for t in completed_turns),
                "max_response_latency": max(t.total_response_latency for t in completed_turns),
            })
        
        return stats
    
    def export_all_turns(self) -> List[Dict[str, Any]]:
        """Export all turn metrics for external analysis."""
        return [turn.to_dict() for turn in self.completed_turns]


def setup_turn_latency_tracking(session: AgentSession) -> TurnLatencyTracker:
    """Set up turn latency tracking for an agent session."""
    tracker = TurnLatencyTracker()
    
    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metric = ev.metrics
        
        # Route metrics to appropriate handler based on type
        if metric.type == "stt_metrics":
            # Check if this STT event indicates an interruption
            if tracker.current_turn and (
                tracker.current_turn.llm_ttft is not None or 
                tracker.current_turn.tts_ttfb is not None
            ):
                # User started speaking while agent was generating or speaking
                tracker.handle_interruption_from_new_stt()
            
            # Start new turn on STT completion (if no current turn)
            if not tracker.current_turn:
                tracker.start_new_turn()
            tracker.update_stt_metrics(metric)
            
        elif metric.type == "eou_metrics":
            tracker.update_eou_metrics(metric)
            
        elif metric.type == "llm_metrics":
            tracker.update_llm_metrics(metric)
            
        elif metric.type == "tts_metrics":
            tracker.update_tts_metrics(metric)
    
    return tracker 