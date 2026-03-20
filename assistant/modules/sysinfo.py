import platform
from datetime import datetime
from assistant.utils.logger import setup_logger

logger = setup_logger()

# Thresholds for auto-pause
CPU_THRESHOLD  = 85   # percent
RAM_THRESHOLD  = 90   # percent
TEMP_THRESHOLD = 75   # Celsius


def _get_psutil():
    try:
        import psutil
        return psutil
    except ImportError:
        return None


def get_temp() -> float | None:
    """Read CPU temperature — Pi thermal zone first, then psutil sensors."""
    try:
        with open('/sys/class/thermal/thermal_zone0/temp') as f:
            return int(f.read().strip()) / 1000.0
    except Exception:
        pass
    psutil = _get_psutil()
    if psutil:
        try:
            sensors = psutil.sensors_temperatures()
            for key in ('cpu_thermal', 'coretemp', 'k10temp'):
                if key in sensors and sensors[key]:
                    return sensors[key][0].current
        except Exception:
            pass
    return None


def get_stats() -> dict:
    psutil = _get_psutil()
    if not psutil:
        return {'error': 'psutil not installed'}

    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
    hours, rem = divmod(int(uptime.total_seconds()), 3600)
    minutes, _ = divmod(rem, 60)
    temp = get_temp()

    return {
        'cpu':          cpu,
        'ram_pct':      ram.percent,
        'ram_used_mb':  ram.used   // 1024 ** 2,
        'ram_total_mb': ram.total  // 1024 ** 2,
        'disk_pct':     disk.percent,
        'disk_used_gb': disk.used  // 1024 ** 3,
        'disk_total_gb':disk.total // 1024 ** 3,
        'uptime':       f"{hours}h {minutes}m",
        'temp':         temp,
    }


def check_thresholds(stats: dict) -> list[str]:
    """Return warning strings for any exceeded thresholds."""
    if 'error' in stats:
        return []
    warnings = []
    if stats['cpu'] >= CPU_THRESHOLD:
        warnings.append(f"CPU at {stats['cpu']}% (limit: {CPU_THRESHOLD}%)")
    if stats['ram_pct'] >= RAM_THRESHOLD:
        warnings.append(f"RAM at {stats['ram_pct']}% (limit: {RAM_THRESHOLD}%)")
    if stats['temp'] is not None and stats['temp'] >= TEMP_THRESHOLD:
        warnings.append(f"Temp at {stats['temp']:.1f}°C (limit: {TEMP_THRESHOLD}°C)")
    return warnings


def handle(_args: str = '') -> str:
    stats = get_stats()
    if 'error' in stats:
        return f"sysinfo unavailable: {stats['error']}"

    temp_str = f"{stats['temp']:.1f}°C" if stats['temp'] is not None else "N/A"
    lines = [
        "System Info",
        f"CPU:  {stats['cpu']}%",
        f"RAM:  {stats['ram_pct']}%  ({stats['ram_used_mb']} MB / {stats['ram_total_mb']} MB)",
        f"Disk: {stats['disk_pct']}%  ({stats['disk_used_gb']} GB / {stats['disk_total_gb']} GB)",
        f"Temp: {temp_str}",
        f"Up:   {stats['uptime']}",
        f"OS:   {platform.system()} {platform.release()}",
    ]
    warnings = check_thresholds(stats)
    if warnings:
        lines.append("")
        lines.extend(f"WARNING: {w}" for w in warnings)
    return '\n'.join(lines)
