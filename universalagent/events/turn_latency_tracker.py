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
    
    # TTS Metrics
    tts_ttfb: Optional[float] = None  # Time to First Byte
    tts_total_duration: Optional[float] = None
    tts_audio_duration: Optional[float] = None
    
    # Calculated Total Latencies
    total_response_latency: Optional[float] = None
    speech_id: Optional[str] = None
    
    def calculate_total_latency(self) -> Optional[float]:
        """Calculate total conversation latency as per LiveKit docs:
        total_latency = eou.end_of_utterance_delay + llm.ttft + tts.ttfb
        """
        if all([self.eou_end_of_utterance_delay, self.llm_ttft, self.tts_ttfb]):
            self.total_response_latency = (
                self.eou_end_of_utterance_delay + 
                self.llm_ttft + 
                self.tts_ttfb
            )
            return self.total_response_latency
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/export."""
        return {
            "turn_id": self.turn_id,
            "start_timestamp": self.start_timestamp,
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
                "tokens_per_second": self.llm_tokens_per_second
            },
            "tts": {
                "ttfb": self.tts_ttfb,
                "total_duration": self.tts_total_duration,
                "audio_duration": self.tts_audio_duration
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
        
    def start_new_turn(self) -> str:
        """Start tracking a new conversational turn."""
        self.turn_counter += 1
        turn_id = f"turn_{self.turn_counter}_{int(time.time())}"
        
        # Complete previous turn if exists
        if self.current_turn:
            self.complete_current_turn()
        
        self.current_turn = TurnLatencyMetrics(
            turn_id=turn_id,
            start_timestamp=time.time()
        )
        
        logger.info(f"🔄 Started tracking turn: {turn_id}")
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
        
        logger.debug(f"🎤 TTS metrics for {self.current_turn.turn_id}: "
                    f"ttfb={tts_metrics.ttfb:.3f}s, "
                    f"duration={tts_metrics.duration:.3f}s")
        
        # Auto-complete turn when TTS starts (agent begins speaking)
        self.complete_current_turn()
    
    def complete_current_turn(self):
        """Complete the current turn and calculate final metrics."""
        if not self.current_turn:
            return
            
        # Calculate total latency
        total_latency = self.current_turn.calculate_total_latency()
        
        # Log comprehensive turn summary
        self.log_turn_summary(self.current_turn)
        
        # Store completed turn
        self.completed_turns.append(self.current_turn)
        self.current_turn = None
        
        logger.info(f"✅ Completed turn with total latency: {total_latency:.3f}s" if total_latency else "✅ Completed turn (partial metrics)")
    
    def log_turn_summary(self, turn: TurnLatencyMetrics):
        """Log detailed turn latency summary."""
        logger.info(f"📊 TURN LATENCY SUMMARY - {turn.turn_id}")
        logger.info(f"   📝 STT Duration: {turn.stt_duration:.3f}s" if turn.stt_duration else "   📝 STT Duration: N/A")
        logger.info(f"   🎯 EOU Detection Delay: {turn.eou_end_of_utterance_delay:.3f}s" if turn.eou_end_of_utterance_delay else "   🎯 EOU Detection Delay: N/A")
        logger.info(f"   🧠 LLM Time to First Token: {turn.llm_ttft:.3f}s" if turn.llm_ttft else "   🧠 LLM TTFT: N/A")
        logger.info(f"   🎤 TTS Time to First Byte: {turn.tts_ttfb:.3f}s" if turn.tts_ttfb else "   🎤 TTS TTFB: N/A")
        logger.info(f"   ⏱️  TOTAL RESPONSE LATENCY: {turn.total_response_latency:.3f}s" if turn.total_response_latency else "   ⏱️  TOTAL RESPONSE LATENCY: Incomplete")
        logger.info(f"   ────────────────────────────────")
    
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
        
        # Calculate averages for completed turns with valid metrics
        valid_turns = [t for t in self.completed_turns if t.total_response_latency is not None]
        
        if not valid_turns:
            return {"total_turns": len(self.completed_turns), "message": "No turns with complete metrics"}
        
        return {
            "total_turns": len(self.completed_turns),
            "valid_turns": len(valid_turns),
            "average_response_latency": sum(t.total_response_latency for t in valid_turns) / len(valid_turns),
            "average_stt_duration": sum(t.stt_duration for t in valid_turns if t.stt_duration) / len([t for t in valid_turns if t.stt_duration]),
            "average_eou_delay": sum(t.eou_end_of_utterance_delay for t in valid_turns if t.eou_end_of_utterance_delay) / len([t for t in valid_turns if t.eou_end_of_utterance_delay]),
            "average_llm_ttft": sum(t.llm_ttft for t in valid_turns if t.llm_ttft) / len([t for t in valid_turns if t.llm_ttft]),
            "average_tts_ttfb": sum(t.tts_ttfb for t in valid_turns if t.tts_ttfb) / len([t for t in valid_turns if t.tts_ttfb]),
            "min_response_latency": min(t.total_response_latency for t in valid_turns),
            "max_response_latency": max(t.total_response_latency for t in valid_turns),
        }
    
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
            # Start new turn on STT completion
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