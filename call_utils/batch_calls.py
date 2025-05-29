#!/usr/bin/env python3
"""
This script processes a CSV file containing learner information and makes 
outbound calls to conduct surveys.

Usage:
    python batch_calls.py <csv_file> [--delay SECONDS] [--max-calls NUMBER]

Example:
    python batch_calls.py learners.csv --delay 300 --max-calls 5

The CSV file should have at least two columns:
- phone_number: The phone number with country code (e.g., +1234567890)
- learner_name: The name of the learner

Optional columns:
- time_to_call: Time to make the call (format: HH:MM) - if provided, calls
  will only be placed if the current time is after this time
- prep_goal, current_plan: Additional customer metadata
"""

import os
import asyncio
import sys
import csv
import argparse
import time
from datetime import datetime
from dotenv import load_dotenv
from make_call import make_outbound_call

load_dotenv()

def validate_csv_file(file_path):
    """
    Validate that the CSV file exists and has the required columns.
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist")
        return False
    
    required_columns = ["phone_number", "learner_name"]
    
    try:
        with open(file_path, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for column in required_columns:
                if column not in reader.fieldnames:
                    print(f"Error: CSV file must have a '{column}' column")
                    return False
            
            # Validate first row to check for proper format
            for row in reader:
                if not row["phone_number"].startswith("+"):
                    print(f"Warning: Phone number {row['phone_number']} should include country code (start with +)")
                
                # Check time_to_call format if present
                if "time_to_call" in row and row["time_to_call"]:
                    try:
                        datetime.strptime(row["time_to_call"], "%H:%M")
                    except ValueError:
                        print(f"Error: time_to_call must be in HH:MM format, found: {row['time_to_call']}")
                        return False
                
                # We only need to check the first row
                break
            
            return True
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return False

def should_call_now(row):
    """
    Determine if the call should be placed now based on the time_to_call field.
    
    Args:
        row (dict): Row from the CSV file
        
    Returns:
        bool: True if the call should be placed now
    """
    if "time_to_call" not in row or not row["time_to_call"]:
        return True
    
    try:
        call_time = datetime.strptime(row["time_to_call"], "%H:%M")
        current_time = datetime.now()
        
        # Compare hours and minutes
        if (current_time.hour > call_time.hour or 
            (current_time.hour == call_time.hour and current_time.minute >= call_time.minute)):
            return True
        else:
            return False
    except ValueError:
        # If time_to_call format is invalid, default to making the call
        return True

async def process_csv(file_path, delay, max_calls):
    """
    Process the CSV file and make outbound calls.
    
    Args:
        file_path (str): Path to the CSV file
        delay (int): Delay in seconds between calls
        max_calls (int): Maximum number of calls to make (0 for unlimited)
    """
    call_count = 0
    
    with open(file_path, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            if max_calls > 0 and call_count >= max_calls:
                print(f"Reached maximum number of calls ({max_calls})")
                break
            
            phone_number = row["phone_number"]
            learner_name = row["learner_name"]
            
            # Check if we should make this call now
            if not should_call_now(row):
                print(f"Skipping {learner_name} at {phone_number} - scheduled for {row['time_to_call']}")
                continue
            
            try:
                print(f"Calling {learner_name} at {phone_number}...")
                
                # Prepare additional metadata from CSV
                customer_metadata = {}
                for key, value in row.items():
                    if key not in ["phone_number", "learner_name", "time_to_call"] and value:
                        customer_metadata[key] = value
                
                # Make the call with metadata
                participant, room_name = await make_outbound_call(
                    phone_number=phone_number,
                    customer_name=learner_name,
                    **customer_metadata
                )
                
                print(f"Call initiated for {learner_name} in room {room_name}")
                call_count += 1
                
                if call_count < reader.line_num and delay > 0:
                    print(f"Waiting {delay} seconds before next call...")
                    await asyncio.sleep(delay)
                    
            except Exception as e:
                print(f"Error making call to {phone_number}: {e}")
                # Continue with next row

async def main():
    """Main entry point for the script."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Make batch outbound calls from a CSV file")
    parser.add_argument("csv_file", help="Path to the CSV file containing learner information")
    parser.add_argument("--delay", type=int, default=300, help="Delay in seconds between calls (default: 300)")
    parser.add_argument("--max-calls", type=int, default=0, help="Maximum number of calls to make (default: 0 for unlimited)")
    
    args = parser.parse_args()
    
    # Validate the CSV file
    if not validate_csv_file(args.csv_file):
        sys.exit(1)
    
    # Check environment variables
    required_vars = ["LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET", "SIP_TRUNK_ID"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file or environment")
        sys.exit(1)
    
    # Process the CSV file
    await process_csv(args.csv_file, args.delay, args.max_calls)
    
    print("Batch processing complete")

if __name__ == "__main__":
    asyncio.run(main()) 