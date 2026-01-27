import discord
from discord import app_commands
import os, json, time, datetime

# =====================
# 💰 파일
# =====================
MONEY_FILE = "money.json"
SALARY_LOG = "salary_log.json"

# =====================
# 🏛️ 월급표
# =====================
ROLE_SALARY = {
    "대통령": 6000,
    "국무총리": 5000,

    "장관": 4000,
    "차관": 3000,
    "사원": 2000,

    "국회의장": 3500,
    "국회의원": 2500,

    "최고재판관": 4500,
    "판사": 3500,
    "검사": 3000,
    "변호인": 2000,

    "경찰": 2500
}

PUNISH_ROLE = "재재대상"

# =====================
# 💾 공통 함수
# =====================
def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_money(user_id, amount):
    data = load_json(MONEY_FILE)
    uid = str(user_id)
    data[uid] = data.get(uid, 0) + amount
    save_json(MONEY_FILE, data)

# =====================
# 🤖 클라이언트
# =====================
class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        print("✅ 글로벌 슬래시 커맨드 동기화")


client = MyClient()

# =====================
# 🔹 /핑
# =====================
@client.tree.command(name="핑", description="봇 상태 확인")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"🏓 퐁!\n지연: {round(client.latency * 1000)}ms"
    )

# =====================
# 🔹 /재화
# =====================
@client.tree.command(name="재화", description="내 재화 확인")
async def money(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    money = load_json(MONEY_FILE).get(uid, 0)

    await interaction.response.send_message(
        f"💰 {interaction.user.display_name}님의 재화: {money}원",
        ephemeral=True
    )

@client.tree.command(name="재화설정", description="유저 재화 수동 조정 (관리자 전용)")
@app_commands.describe(
    대상="재화를 조정할 유저",
    금액="추가 또는 차감할 금액",
    방식="add = 지급, sub = 차감"
)
@app_commands.choices(
    방식=[
        app_commands.Choice(name="지급", value="add"),
        app_commands.Choice(name="차감", value="sub")
    ]
)
async def set_money(
    interaction: discord.Interaction,
    대상: discord.Member,
    금액: int,
    방식: app_commands.Choice[str]
):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ 관리자만 사용할 수 있는 명령어입니다.",
            ephemeral=True
        )
        return

    data = load_json(MONEY_FILE)
    uid = str(대상.id)
    현재재화 = data.get(uid, 0)

    if 방식.value == "add":
        새로운재화 = 현재재화 + 금액
    else:
        새로운재화 = max(0, 현재재화 - 금액)

    data[uid] = 새로운재화
    save_json(MONEY_FILE, data)

    await interaction.response.send_message(
        f"💰 **재화 조정 완료**\n"
        f"대상: {대상.display_name}\n"
        f"이전: {현재재화}원\n"
        f"변경 후: {새로운재화}원",
        ephemeral=True
    )


# =====================
# 🔹 /월급지급 (관리자)
# =====================
@client.tree.command(name="월급지급", description="국가 월급 일괄 지급 (관리자 전용)")
async def salary(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ 관리자만 월급을 지급할 수 있습니다.",
            ephemeral=True
        )
        return

    guild = interaction.guild
    today = str(datetime.date.today())
    log = load_json(SALARY_LOG)

    지급수 = 0
    총액 = 0

    for member in guild.members:
        if member.bot:
            continue

        roles = [r.name for r in member.roles]

        # 징계 대상 제외
        if PUNISH_ROLE in roles:
            continue

        uid = str(member.id)

        # 오늘 이미 지급됨
        if log.get(uid) == today:
            continue

        salary = 0

        for role, pay in ROLE_SALARY.items():
            if any(role in r for r in roles):
                salary = max(salary, pay)

        if salary == 0:
            continue

        add_money(member.id, salary)
        log[uid] = today
        지급수 += 1
        총액 += salary

    save_json(SALARY_LOG, log)

    await interaction.response.send_message(
        f"🏦 **국가 월급 지급 완료**\n"
        f"지급 인원: {지급수}명\n"
        f"총 지급액: {총액}원"
    )

# =====================
# 🚀 실행
# =====================
client.run(os.environ["DISCORD_TOKEN"])
