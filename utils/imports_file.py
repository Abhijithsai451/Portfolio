from pathlib import Path
import asyncio
import json
import logging
import os
import re
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import uvicorn
import aiohttp
import prometheus_client
import redis
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Gauge, REGISTRY
from prometheus_client import Histogram, generate_latest
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from fastapi.responses import PlainTextResponse
from utils.monitor import Monitor
