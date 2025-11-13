from webhook_server import app
from telegram_bot import start_bot
import uvicorn
import os

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(start_bot())
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)

