# backend/services/iot_service.py
import asyncio
import logging
import time
import httpx
import re
from typing import Optional
from backend.core.event_bus import event_bus
from backend.database import AsyncSessionLocal
from backend.schemas import SensorPayload, SensorOut
from backend.services.sensor_ingestion import ingest_sensor_internal

logger = logging.getLogger(__name__)

_polling_task: Optional[asyncio.Task] = None
_polling_ip: Optional[str] = None
_is_polling = False

async def start_iot_polling(ip: str):
    global _polling_task, _polling_ip, _is_polling
    if _polling_task and not _polling_task.done():
        _polling_task.cancel()
    
    _polling_ip = ip
    _is_polling = True
    _polling_task = asyncio.create_task(_poll_loop())
    logger.info(f"IoT sensor polling started for IP: {ip}")

async def stop_iot_polling():
    global _is_polling, _polling_task
    _is_polling = False
    if _polling_task:
        _polling_task.cancel()
    logger.info("IoT sensor polling stopped")

def get_polling_status() -> dict:
    return {
        "ip": _polling_ip,
        "active": _is_polling and _polling_task and not _polling_task.done()
    }

async def _poll_loop():
    async with httpx.AsyncClient(timeout=20.0, trust_env=False) as client:
        while _is_polling:
            try:
                # Try root first as it's the most likely endpoint for the text format
                endpoints = ["/", "/sensor", "/data"]
                response = None
                
                for ep in endpoints:
                    try:
                        url = f"http://{_polling_ip}{ep}"
                        res = await client.get(url, timeout=15.0)
                        if res.status_code == 200:
                            response = res
                            break
                        else:
                            logger.info(f"IoT {url} returned {res.status_code}")
                    except Exception as e:
                        logger.info(f"IoT {url} error: {type(e).__name__} - {str(e)}")
                        continue
                
                if not response:
                    logger.warning(f"Could not reach any endpoint on IoT sensor at {_polling_ip}")
                    await asyncio.sleep(5)
                    continue

                text = response.text
                logger.info(f"IoT Raw Data: {text[:100]}...")
                
                # Regex parsing for text format (as seen in user screenshot patterns)
                def extract(pattern, default=0.0):
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        try:
                            return float(match.group(1))
                        except:
                            pass
                    return default

                # Map common patterns (allowing for HTML tags like <br> or <b>)
                temp = extract(r"DHT Temp[^<\d]*[:\s]+([\d\.]+)", 0.0)
                hum  = extract(r"Humidity[^<\d]*[:\s]+([\d\.]+)", 0.0)
                ds_temp = extract(r"DS18B20 Temp[^<\d]*[:\s]+([\d\.]+)", 0.0)
                smoke = extract(r"Smoke Value[^<\d]*[:\s]+([\d\.]+)", 0.0)
                gas   = extract(r"gas[^<\d]*[:\s]+([\d\.]+)", 0.0)
                lat   = extract(r"Lat(?:itude)?[^<\d]*[:\s]+([\d\.]+)", 22.5726)
                lng   = extract(r"Long(?:itude)?[^<\d]*[:\s]+([\d\.]+)", 88.3639)

                # Fallback to JSON if it looks like JSON
                if not any([temp, hum, smoke, ds_temp]) and "{" in text:
                    try:
                        data = response.json()
                        temp = data.get("temperature", data.get("temp", 0.0))
                        hum  = data.get("humidity", data.get("hum", 0.0))
                        ds_temp = data.get("ds18b20_temp", 0.0)
                        smoke = data.get("smoke", data.get("smoke_value", 0.0))
                        gas   = data.get("gas", 0.0)
                        lat   = data.get("lat", 22.5726)
                        lng   = data.get("lng", 88.3639)
                    except:
                        pass

                payload = SensorPayload(
                    device_id=f"iot-{_polling_ip}",
                    temperature=temp,
                    smoke=smoke,
                    gas=gas,
                    humidity=hum,
                    ds18b20_temp=ds_temp,
                    lat=lat,
                    lng=lng
                )

                async with AsyncSessionLocal() as db:
                    await ingest_sensor_internal(payload, db)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error polling IoT sensor: {e}")
            
            await asyncio.sleep(5)
