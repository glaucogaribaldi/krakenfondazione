import subprocess
import time
import json
import os

class TelemetryProfiler:
    """
    SentinelProf - Telemetry & Diagnostic Profiler
    Monitors inference latency, VPS GPU resource usage (NVIDIA Tesla T4),
    slippage leakage, and margin warnings.
    """
    def __init__(self, log_path="./data/telemetry_profile.json", vps_ip="100.73.54.72"):
        self.log_path = log_path
        self.vps_ip = vps_ip
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def get_gpu_metrics(self):
        """Executes nvidia-smi over SSH to profile the remote VPS GPU resource utilization"""
        # Command to query VPS GPUs
        cmd = f"ssh -o StrictHostKeyChecking=no tre@{self.vps_ip} 'nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null'"
        try:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            if res.returncode == 0 and res.stdout.strip():
                lines = res.stdout.strip().split('\n')
                gpus = []
                for idx, line in enumerate(lines):
                    parts = [x.strip() for x in line.split(',')]
                    if len(parts) == 3:
                        gpus.append({
                            "gpu_index": idx,
                            "utilization_pct": float(parts[0]),
                            "memory_used_mb": float(parts[1]),
                            "memory_total_mb": float(parts[2]),
                            "memory_utilization_pct": round((float(parts[1]) / float(parts[2]) * 100), 2)
                        })
                return gpus
            else:
                return [{"status": "offline", "reason": "No GPU detected or SSH failed"}]
        except Exception as e:
            return [{"status": "error", "reason": str(e)}]

    def log_metrics(self, latency_ms, margin_used_pct, slippage_leakage_pct, status="OK"):
        """Logs a single telemetry sweep to disk"""
        gpu_metrics = self.get_gpu_metrics()
        
        sweep = {
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "inference_latency_ms": latency_ms,
            "margin_utilization_pct": margin_used_pct,
            "slippage_leakage_pct": slippage_leakage_pct,
            "status": status,
            "vps_gpus": gpu_metrics
        }
        
        # Read existing log
        history = []
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, "r") as f:
                    history = json.load(f)
            except Exception:
                pass
                
        history.append(sweep)
        # Keep last 50 sweeps
        history = history[-50:]
        
        with open(self.log_path, "w") as f:
            json.dump(history, f, indent=2)
            
        return sweep
