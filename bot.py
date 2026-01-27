import discord
from discord import app_commands
import os, json, datetime

# =====================
# 💰 파일
# =====================
MONEY_FILE = "money.json"
SALARY_LOG = "salary_log.json"
SALARY_FILE = "salary.json"  # 역할별 월급 저장용

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
# 💾 월급 파일
# =====================
def load_salary():
    if not os.path.exists(SALARY_FILE):
        return {}
    with open(SALARY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_salary():
    with open(SALARY_FILE, "w", encoding="utf-8") as f:
        json.dump(ROLE_SALARY, f, ensure_ascii=False, indent=2)

# 처음 실행 시 파일 불러오기
ROLE_SALARY = load_salary()

# =====================
# 🤖 클라이언트
# =====================
PUNISH_ROLE = "재재대상"

class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # 앱 켜질 때 자동 동기화
        print("🚀 자동 동기화 시작...")
        try:
            # 길드 전용 동기화 예시: guild_id = YOUR_GUILD_ID
            synced = await self.tree.sync()  # 글로벌 동기화
            print(f"✅ 자동 동기화 완료! 등록된 명령어 수: {len(synced)}개")
        except Exception as e:
            print(f"❌ 자동 동기화 실패: {e}")

    async def setup_hook(self):
        print("✅ setup_hook 완료 (동기화 필요 시 /동기화 사용)")

client = MyClient()

# =====================
# 🔹 /법률
# =====================
@client.tree.command(name="법률", description="국가 법률 웹사이트 접속")
async def law(interaction: discord.Interaction):
    await interaction.response.send_message(
        "📜 국가 법률 웹사이트: [바로가기](https://minty-developer.github.io/Country_server/)",
        ephemeral=True
    )


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
# 🔹 /동기화 (관리자 전용)
# =====================
@client.tree.command(name="동기화", description="슬래시 명령어 수동 동기화 (관리자 전용)")
async def sync_commands(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ 관리자만 사용할 수 있는 명령어입니다.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)
    try:
        synced = await client.tree.sync()
        await interaction.followup.send(
            f"✅ **동기화 완료**\n등록된 명령어 수: {len(synced)}개",
            ephemeral=True
        )
    except Exception as e:
        await interaction.followup.send(
            f"❌ 동기화 실패\n```{e}```",
            ephemeral=True
        )

# =====================
# 🔹 월급 관리 (관리자 전용)
# =====================
# 월급 수정
@client.tree.command(name="월급수정", description="역할별 월급 수정 (관리자 전용)")
@app_commands.describe(역할="월급을 수정할 역할 이름", 금액="설정할 월급 금액")
async def set_salary(interaction: discord.Interaction, 역할: str, 금액: int):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ 관리자만 사용 가능", ephemeral=True)
        return

    ROLE_SALARY[역할] = 금액
    save_salary()
    await interaction.response.send_message(f"💰 **{역할} 월급 수정 완료**\n새 월급: {금액}원", ephemeral=True)

# 새 역할 월급 설정
@client.tree.command(name="월급설정", description="새 역할 월급 최초 설정 (관리자 전용)")
@app_commands.describe(역할="새로 만든 역할 이름", 금액="설정할 월급 금액")
async def add_role_salary(interaction: discord.Interaction, 역할: str, 금액: int):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ 관리자만 사용 가능", ephemeral=True)
        return

    if 역할 in ROLE_SALARY:
        await interaction.response.send_message("⚠️ 이미 존재하는 역할입니다.", ephemeral=True)
        return

    ROLE_SALARY[역할] = 금액
    save_salary()
    await interaction.response.send_message(f"✅ **새 역할 {역할} 월급 설정 완료**\n월급: {금액}원", ephemeral=True)

# 월급 삭제
@client.tree.command(name="월급삭제", description="역할별 월급 삭제 (관리자 전용)")
@app_commands.describe(역할="삭제할 역할 이름")
async def remove_role_salary(interaction: discord.Interaction, 역할: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ 관리자만 사용 가능", ephemeral=True)
        return

    if 역할 not in ROLE_SALARY:
        await interaction.response.send_message("⚠️ 월급표에 없는 역할입니다.", ephemeral=True)
        return

    del ROLE_SALARY[역할]
    save_salary()
    await interaction.response.send_message(f"🗑️ **{역할} 역할 월급 삭제 완료**", ephemeral=True)

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

        salary_amount = 0
        for role, pay in ROLE_SALARY.items():
            if role in roles:
                salary_amount = max(salary_amount, pay)

        if salary_amount == 0:
            continue

        add_money(member.id, salary_amount)
        log[uid] = today
        지급수 += 1
        총액 += salary_amount

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
