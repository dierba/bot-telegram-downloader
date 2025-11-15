import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# Pega o token das variáveis de ambiente
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')

def get_ydl_opts(output_path):
    return {
        'format': 'best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
    }

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = """
🔥 *Bot Downloader de Vídeos*

Envie um link de:
- YouTube / YouTube Shorts
- Instagram (Posts, Reels, Stories)
- TikTok

Eu vou baixar e enviar o vídeo para você!

⚡ Suporta vídeos de até 50MB
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text("❌ Por favor, envie um link válido!")
        return
    
    supported = any(platform in url.lower() for platform in 
                   ['youtube.com', 'youtu.be', 'instagram.com', 'tiktok.com'])
    
    if not supported:
        await update.message.reply_text(
            "❌ Plataforma não suportada!\n"
            "Suporto: YouTube, Instagram, TikTok"
        )
        return
    
    status_msg = await update.message.reply_text("⏳ Baixando vídeo...")
    
    try:
        video_file = f"video_{update.message.message_id}.mp4"
        ydl_opts = get_ydl_opts(video_file)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await status_msg.edit_text("⏳ Processando vídeo...")
            info = await asyncio.to_thread(ydl.extract_info, url, download=True)
            title = info.get('title', 'Video')
        
        if not os.path.exists(video_file):
            await status_msg.edit_text("❌ Erro ao baixar o vídeo!")
            return
        
        file_size = os.path.getsize(video_file)
        if file_size > 50 * 1024 * 1024:
            os.remove(video_file)
            await status_msg.edit_text(
                "❌ Vídeo muito grande (>50MB)!\n"
                "O Telegram tem limite de 50MB para bots."
            )
            return
        
        await status_msg.edit_text("⏳ Enviando vídeo...")
        
        with open(video_file, 'rb') as video:
            await update.message.reply_video(
                video=video,
                caption=f"✅ {title[:200]}",
                supports_streaming=True
            )
        
        await status_msg.delete()
        os.remove(video_file)
        
    except Exception as e:
        error_msg = str(e)
        if "private" in error_msg.lower():
            await status_msg.edit_text("❌ Vídeo privado ou não acessível!")
        elif "unavailable" in error_msg.lower():
            await status_msg.edit_text("❌ Vídeo não disponível!")
        else:
            await status_msg.edit_text(f"❌ Erro ao processar: {error_msg[:100]}")
        
        if os.path.exists(video_file):
            os.remove(video_file)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📖 *Como usar:*

1️⃣ Copie o link do vídeo
2️⃣ Envie o link aqui
3️⃣ Aguarde o download
4️⃣ Receba seu vídeo!

*Plataformas suportadas:*
- YouTube (vídeos e Shorts)
- Instagram (Posts, Reels)
- TikTok

⚠️ *Limitações:*
- Vídeos até 50MB
- Apenas vídeos públicos
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

def main():
    print("🤖 Iniciando bot...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    print("✅ Bot rodando!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
