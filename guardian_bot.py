"""
Guardian Bot - Discord Moderasyon ve Reputation Botu
Tek dosya versiyonu - Bulut platformlarında çalıştırmak için
"""

import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
import aiosqlite
import json
import re
from datetime import datetime
from dotenv import load_dotenv

# Opsiyonel: Gemini AI
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ google-generativeai yüklü değil, AI özellikleri devre dışı")

load_dotenv()

# ==================== YAPILANDIRMA ====================

# Reputation Ayarları
STARTING_REPUTATION = 100
MAX_REPUTATION = 1000
MIN_REPUTATION = 0

# Ceza Puanları
PROFANITY_PENALTY = 10
INSULT_PENALTY = 15
SEVERE_PENALTY = 25

# Ceza Eşikleri
MUTE_THRESHOLD = 30
KICK_THRESHOLD = 10
BAN_THRESHOLD = 0

# Türkçe Küfür Listesi
TURKISH_PROFANITY = [
    "aptal", "salak", "gerizekalı", "mal", "dangalak", "ahmak",
    "budala", "mankafa", "şerefsiz", "namussuz", "haysiyetsiz",
    "pislik", "sürtük", "kaltak", "orospu", "piç", "gavat",
    "amk", "aq", "mk", "sg", "siktir", "bok", "göt", "yarrak",
    "am", "s*k", "a*k", "o*ospu", "p*ç"
]

INSULT_PATTERNS = [
    "ananı", "bacını", "sülaleni", "soyunu", "sopunu",
    "geberteyim", "öldüreyim", "geberesin", "ölün",
    "defol", "kaybol", "çık git"
]

# Gemini Ayarları
GEMINI_MODEL = "gemini-1.5-flash"
GEMINI_SAFETY_PROMPT = """
Aşağıdaki Türkçe mesajı analiz et ve JSON formatında yanıt ver:
- is_toxic: mesajda küfür, hakaret veya zararlı içerik var mı (true/false)
- severity: zararlılık seviyesi (0-10 arası)
- reason: kısa açıklama (Türkçe)
- category: kategori (clean/profanity/insult/threat/spam/other)

Mesaj: "{message}"

Sadece JSON formatında yanıt ver.
"""

# ==================== VERİTABANI ====================

DATABASE_PATH = "reputation.db"

async def init_database():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER,
                guild_id INTEGER,
                username TEXT,
                reputation INTEGER DEFAULT 100,
                total_messages INTEGER DEFAULT 0,
                warnings INTEGER DEFAULT 0,
                last_active TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, guild_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reputation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                guild_id INTEGER,
                change_amount INTEGER,
                reason TEXT,
                message_content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()
        print("✅ Veritabanı hazır")

async def get_user(user_id: int, guild_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM users WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id)
        )
        return await cursor.fetchone()

async def create_user(user_id: int, guild_id: int, username: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO users (user_id, guild_id, username, reputation, last_active)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, guild_id, username, STARTING_REPUTATION, datetime.now()))
        await db.commit()

async def update_reputation(user_id: int, guild_id: int, change: int, reason: str, message_content: str = None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT reputation FROM users WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id)
        )
        result = await cursor.fetchone()
        
        if result:
            current_rep = result[0]
            new_rep = max(MIN_REPUTATION, min(MAX_REPUTATION, current_rep + change))
            
            await db.execute("""
                UPDATE users SET reputation = ?, last_active = ?
                WHERE user_id = ? AND guild_id = ?
            """, (new_rep, datetime.now(), user_id, guild_id))
            
            await db.execute("""
                INSERT INTO reputation_history (user_id, guild_id, change_amount, reason, message_content)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, guild_id, change, reason, message_content[:500] if message_content else None))
            
            await db.commit()
            return new_rep
    return None

async def increment_warnings(user_id: int, guild_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            UPDATE users SET warnings = warnings + 1
            WHERE user_id = ? AND guild_id = ?
        """, (user_id, guild_id))
        await db.commit()

async def increment_messages(user_id: int, guild_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            UPDATE users SET total_messages = total_messages + 1, last_active = ?
            WHERE user_id = ? AND guild_id = ?
        """, (datetime.now(), user_id, guild_id))
        await db.commit()

async def get_leaderboard(guild_id: int, limit: int = 10):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT user_id, username, reputation, total_messages, warnings
            FROM users WHERE guild_id = ?
            ORDER BY reputation DESC LIMIT ?
        """, (guild_id, limit))
        return await cursor.fetchall()

async def get_user_history(user_id: int, guild_id: int, limit: int = 10):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT change_amount, reason, created_at
            FROM reputation_history
            WHERE user_id = ? AND guild_id = ?
            ORDER BY created_at DESC LIMIT ?
        """, (user_id, guild_id, limit))
        return await cursor.fetchall()

# ==================== KÜFÜR ALGILAMA ====================

class ProfanityDetector:
    def __init__(self):
        self.profanity_list = set(word.lower() for word in TURKISH_PROFANITY)
        self.char_replacements = {
            '4': 'a', '@': 'a', '0': 'o', '1': 'i', '!': 'i',
            '3': 'e', '$': 's', '5': 's', '7': 't', '+': 't',
            '*': '', '.': '', '-': '', '_': ''
        }
    
    def _normalize_text(self, text: str) -> str:
        text = text.lower()
        for old, new in self.char_replacements.items():
            text = text.replace(old, new)
        text = re.sub(r'(.)\1{2,}', r'\1\1', text)
        return text
    
    def check(self, message: str) -> dict:
        normalized = self._normalize_text(message)
        words = re.findall(r'\b\w+\b', normalized)
        
        matched_words = []
        has_profanity = False
        has_insult = False
        severity = 'clean'
        penalty = 0
        
        for word in words:
            if word in self.profanity_list:
                matched_words.append(word)
                has_profanity = True
        
        for profanity in self.profanity_list:
            if profanity in normalized and profanity not in matched_words:
                matched_words.append(profanity)
                has_profanity = True
        
        for pattern in INSULT_PATTERNS:
            if pattern.lower() in normalized:
                has_insult = True
                if pattern not in matched_words:
                    matched_words.append(pattern)
        
        if has_profanity or has_insult:
            severe_words = ['orospu', 'piç', 'siktir', 'amk', 'aq', 'ananı', 'bacını']
            if any(sw in normalized for sw in severe_words):
                severity = 'severe'
                penalty = SEVERE_PENALTY
            elif has_insult:
                severity = 'moderate'
                penalty = INSULT_PENALTY
            else:
                severity = 'mild'
                penalty = PROFANITY_PENALTY
        
        return {
            'has_profanity': has_profanity,
            'has_insult': has_insult,
            'severity': severity,
            'matched_words': matched_words,
            'penalty': penalty
        }

# ==================== GEMINI AI ====================

class GeminiAI:
    def __init__(self, api_key: str):
        if GEMINI_AVAILABLE:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(GEMINI_MODEL)
            self.chat_sessions = {}
        else:
            self.model = None
    
    async def check_toxicity(self, message: str) -> dict:
        if not self.model:
            return {'is_toxic': False, 'severity': 0, 'reason': 'AI devre dışı', 'category': 'unknown'}
        
        try:
            prompt = GEMINI_SAFETY_PROMPT.format(message=message)
            response = await self.model.generate_content_async(prompt)
            response_text = response.text.strip()
            
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            return json.loads(response_text.strip())
        except:
            return {'is_toxic': False, 'severity': 0, 'reason': 'Analiz hatası', 'category': 'error'}
    
    async def chat(self, user_id: int, message: str) -> str:
        if not self.model:
            return "AI şu anda kullanılamıyor."
        
        try:
            if user_id not in self.chat_sessions:
                self.chat_sessions[user_id] = self.model.start_chat(history=[])
            
            response = await self.chat_sessions[user_id].send_message_async(message)
            return response.text
        except Exception as e:
            return f"Hata: {e}"

# ==================== BOT ====================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

class GuardianBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=os.getenv('BOT_PREFIX', '!'),
            intents=intents,
            help_command=None
        )
        
        self.profanity_detector = ProfanityDetector()
        
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key and GEMINI_AVAILABLE:
            self.gemini = GeminiAI(gemini_key)
            print("✅ Gemini AI başlatıldı")
        else:
            self.gemini = None
    
    async def setup_hook(self):
        await init_database()
        await self.tree.sync()
        print("✅ Komutlar senkronize edildi")
    
    async def on_ready(self):
        print(f"✅ {self.user.name} aktif! ({len(self.guilds)} sunucu)")
        await self.change_presence(activity=discord.Activity(
            type=discord.ActivityType.watching, name="sunucuyu koruyorum 🛡️"
        ))
    
    async def on_member_join(self, member: discord.Member):
        if not member.bot:
            await create_user(member.id, member.guild.id, member.display_name)
    
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        
        user_data = await get_user(message.author.id, message.guild.id)
        if not user_data:
            await create_user(message.author.id, message.guild.id, message.author.display_name)
        
        await increment_messages(message.author.id, message.guild.id)
        
        if not message.author.guild_permissions.moderate_members:
            await self.moderate_message(message)
        
        await self.process_commands(message)
    
    async def moderate_message(self, message: discord.Message):
        local_check = self.profanity_detector.check(message.content)
        
        is_toxic = local_check['has_profanity'] or local_check['has_insult']
        penalty = local_check['penalty']
        severity = local_check['severity']
        reason = f"Yasaklı kelimeler: {', '.join(local_check['matched_words'][:3])}" if local_check['matched_words'] else ""
        
        # AI kontrolü (opsiyonel)
        if self.gemini and not is_toxic:
            ai_result = await self.gemini.check_toxicity(message.content)
            if ai_result.get('is_toxic'):
                is_toxic = True
                if ai_result['severity'] >= 7:
                    severity = 'severe'
                    penalty = SEVERE_PENALTY
                elif ai_result['severity'] >= 4:
                    severity = 'moderate'
                    penalty = INSULT_PENALTY
                else:
                    severity = 'mild'
                    penalty = PROFANITY_PENALTY
                reason = ai_result.get('reason', 'AI tespit')
        
        if is_toxic and penalty > 0:
            new_rep = await update_reputation(
                message.author.id, message.guild.id, -penalty, reason, message.content
            )
            await increment_warnings(message.author.id, message.guild.id)
            
            # Uyarı gönder
            emoji = "🚨" if severity == 'severe' else "⚠️" if severity == 'moderate' else "💡"
            embed = discord.Embed(
                description=f"{emoji} **Uyarı!** {reason}",
                color=discord.Color.red() if severity == 'severe' else discord.Color.orange()
            )
            embed.set_footer(text=f"📉 -{penalty} rep | Kalan: {new_rep}")
            
            try:
                await message.reply(embed=embed, delete_after=30)
            except:
                pass
            
            # Ceza kontrolü
            if new_rep <= BAN_THRESHOLD:
                try:
                    await message.author.ban(reason="Reputation 0")
                except:
                    pass
            elif new_rep <= MUTE_THRESHOLD:
                try:
                    await message.author.timeout(
                        discord.utils.utcnow() + discord.timedelta(minutes=10),
                        reason="Düşük reputation"
                    )
                except:
                    pass

bot = GuardianBot()

# ==================== KOMUTLAR ====================

@bot.tree.command(name="rep", description="Reputation puanını göster")
async def reputation(interaction: discord.Interaction, member: discord.Member = None):
    target = member or interaction.user
    user_data = await get_user(target.id, interaction.guild_id)
    
    if not user_data:
        await create_user(target.id, interaction.guild_id, target.display_name)
        user_data = await get_user(target.id, interaction.guild_id)
    
    rep = user_data['reputation']
    
    if rep >= 500: level, color = "🌟 Efsane", discord.Color.gold()
    elif rep >= 300: level, color = "💎 Elit", discord.Color.purple()
    elif rep >= 200: level, color = "🥇 Deneyimli", discord.Color.blue()
    elif rep >= 100: level, color = "🥈 Normal", discord.Color.green()
    elif rep >= 50: level, color = "🥉 Dikkatli", discord.Color.orange()
    else: level, color = "⚠️ Riskli", discord.Color.red()
    
    embed = discord.Embed(title=f"📊 {target.display_name}", color=color)
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="Reputation", value=f"**{rep}**", inline=True)
    embed.add_field(name="Seviye", value=level, inline=True)
    embed.add_field(name="Mesaj", value=user_data['total_messages'], inline=True)
    embed.add_field(name="Uyarı", value=f"⚠️ {user_data['warnings']}", inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="siralama", description="Reputation sıralaması")
async def leaderboard(interaction: discord.Interaction):
    leaders = await get_leaderboard(interaction.guild_id, 10)
    
    if not leaders:
        await interaction.response.send_message("Henüz sıralamada kimse yok!", ephemeral=True)
        return
    
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    desc = ""
    for i, user in enumerate(leaders):
        member = interaction.guild.get_member(user['user_id'])
        name = member.display_name if member else user['username']
        desc += f"{medals[i]} **{name}** - {user['reputation']} puan\n"
    
    embed = discord.Embed(title="🏆 Sıralama", description=desc, color=discord.Color.gold())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="uyar", description="Üyeyi uyar")
@app_commands.default_permissions(moderate_members=True)
async def warn(interaction: discord.Interaction, member: discord.Member, sebep: str, puan: int = 10):
    if member.bot:
        await interaction.response.send_message("Botları uyaramazsın!", ephemeral=True)
        return
    
    user_data = await get_user(member.id, interaction.guild_id)
    if not user_data:
        await create_user(member.id, interaction.guild_id, member.display_name)
    
    new_rep = await update_reputation(member.id, interaction.guild_id, -abs(puan), f"Mod: {sebep}")
    await increment_warnings(member.id, interaction.guild_id)
    
    embed = discord.Embed(title="⚠️ Uyarı", color=discord.Color.orange())
    embed.add_field(name="Üye", value=member.mention, inline=True)
    embed.add_field(name="Ceza", value=f"-{abs(puan)}", inline=True)
    embed.add_field(name="Sebep", value=sebep, inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="odul", description="Ödül ver")
@app_commands.default_permissions(moderate_members=True)
async def reward(interaction: discord.Interaction, member: discord.Member, sebep: str, puan: int = 5):
    if member.bot:
        await interaction.response.send_message("Botlara ödül veremezsin!", ephemeral=True)
        return
    
    user_data = await get_user(member.id, interaction.guild_id)
    if not user_data:
        await create_user(member.id, interaction.guild_id, member.display_name)
    
    new_rep = await update_reputation(member.id, interaction.guild_id, abs(puan), f"Ödül: {sebep}")
    
    embed = discord.Embed(title="🎉 Ödül!", color=discord.Color.green())
    embed.add_field(name="Üye", value=member.mention, inline=True)
    embed.add_field(name="Ödül", value=f"+{abs(puan)}", inline=True)
    embed.add_field(name="Sebep", value=sebep, inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="sor", description="AI'a soru sor")
async def ask(interaction: discord.Interaction, soru: str):
    await interaction.response.defer(thinking=True)
    
    if not bot.gemini:
        await interaction.followup.send("AI şu anda kullanılamıyor.")
        return
    
    response = await bot.gemini.chat(interaction.user.id, soru)
    if len(response) > 2000:
        response = response[:1997] + "..."
    
    embed = discord.Embed(description=response, color=discord.Color.blue())
    embed.set_author(name=f"🤖 {interaction.user.display_name} sordu:")
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="yardim", description="Yardım menüsü")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="🛡️ Guardian Bot", color=discord.Color.blue())
    embed.add_field(name="📊 Reputation", value="`/rep` `/siralama`", inline=True)
    embed.add_field(name="🛡️ Moderasyon", value="`/uyar` `/odul`", inline=True)
    embed.add_field(name="🤖 AI", value="`/sor`", inline=True)
    embed.set_footer(text="Küfür/hakaret otomatik algılanır")
    
    await interaction.response.send_message(embed=embed)

# ==================== BAŞLAT ====================

def main():
    token = os.getenv('DISCORD_TOKEN')
    
    if not token:
        print("❌ DISCORD_TOKEN bulunamadı!")
        print("Ortam değişkeni olarak DISCORD_TOKEN ayarla.")
        return
    
    print("🚀 Guardian Bot başlatılıyor...")
    bot.run(token)

if __name__ == "__main__":
    main()
