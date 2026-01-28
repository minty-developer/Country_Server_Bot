import discord
from discord import app_commands
import os, json, datetime

# =====================
# 📁 파일
# =====================
MONEY_FILE = "money.json"
SALARY_FILE = "salary.json"
SALARY_LOG = "salary_log.json"
FINE_FILE = "fine.json"

PUNISH_ROLE = "재재대상"
FINE_ROLE = "벌금대상"

# =====================
# 💾 공통 JSON 함수
# =====================
def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =====================
# 💰 재화
# =====================
def add_money(user_id, amount):
    data = load_json(MONEY_FILE)
    uid = str(user_id)
    data[uid] = data.get(uid, 0) + amount
    save_json(MONEY_FILE, data)

# =====================
# 💼 월급
# =====================
ROLE_SALARY = load_json(SALARY_FILE)

def save_salary():
    save_json(SALARY_FILE, ROLE_SALARY)

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
        synced = await self.tree.sync()
        print(f"✅ 슬래시 명령어 자동 동기화 완료 ({len(synced)}개)")

client = MyClient()

# =====================
# 🔹 기본 명령어
# =====================
@client.tree.command(name="핑", description="봇의 지연 시간을 확인합니다.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"🏓 퐁! {round(client.latency * 1000)}ms"
    )

@client.tree.command(name="재화", description="내 현재 재화를 확인합니다.")
async def my_money(interaction: discord.Interaction):
    data = load_json(MONEY_FILE)
    money = data.get(str(interaction.user.id), 0)
    await interaction.response.send_message(
        f"💰 내 재화: {money}원",
        ephemeral=True
    )

# =====================
# 🔹 재화 보기 (관리자)
# =====================
@client.tree.command(
    name="재화보기",
    description="다른 유저의 재화를 확인합니다. (관리자 전용)"
)
@app_commands.describe(대상="재화를 확인할 유저")
async def check_money(interaction: discord.Interaction, 대상: discord.Member):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ 관리자 전용", ephemeral=True)

    money = load_json(MONEY_FILE).get(str(대상.id), 0)
    await interaction.response.send_message(
        f"💰 {대상.display_name} : {money}원",
        ephemeral=True
    )

# =====================
# 🔹 재화 설정 (관리자)
# =====================
@client.tree.command(
    name="재화설정",
    description="유저의 재화를 지급하거나 차감합니다. (관리자 전용)"
)
@app_commands.describe(대상="유저", 금액="금액", 방식="지급 또는 차감")
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
        return await interaction.response.send_message("❌ 관리자 전용", ephemeral=True)

    data = load_json(MONEY_FILE)
    uid = str(대상.id)
    cur = data.get(uid, 0)

    data[uid] = cur + 금액 if 방식.value == "add" else max(0, cur - 금액)
    save_json(MONEY_FILE, data)

    await interaction.response.send_message(
        f"✅ {대상.display_name} 재화 수정 완료",
        ephemeral=True
    )

# =====================
# 🔹 벌금 부과 (관리자)
# =====================
@client.tree.command(
    name="벌금부과",
    description="유저에게 벌금을 부과합니다. (관리자 전용)"
)
@app_commands.describe(대상="유저", 금액="벌금 금액")
async def fine_add(interaction: discord.Interaction, 대상: discord.Member, 금액: int):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ 관리자 전용", ephemeral=True)

    fines = load_json(FINE_FILE)
    fines[str(대상.id)] = 금액
    save_json(FINE_FILE, fines)

    role = discord.utils.get(interaction.guild.roles, name=FINE_ROLE)
    if role:
        await 대상.add_roles(role)

    await interaction.response.send_message(
        f"⚖️ **벌금 부과 완료**\n대상: {대상.display_name}\n금액: {금액}원",
        ephemeral=True
    )

    # 📩 대상 DM 알림
    try:
        await 대상.send(
            f"⚠️ **벌금이 부과되었습니다**\n\n"
            f"금액: {금액}원\n"
            f"💡 `/벌금납부` 명령어로 납부할 수 있습니다."
        )
    except discord.Forbidden:
        pass  # DM 차단 시 무시

# =====================
# 🔹 벌금 납부 (본인)
# =====================
@client.tree.command(
    name="벌금납부",
    description="부과된 벌금을 납부합니다."
)
async def pay_fine(interaction: discord.Interaction):
    member = interaction.user
    uid = str(member.id)

    fines = load_json(FINE_FILE)

    if uid not in fines:
        return await interaction.response.send_message(
            "❌ 납부할 벌금이 없습니다.",
            ephemeral=True
        )

    fine = fines[uid]

    money = load_json(MONEY_FILE)
    cur = money.get(uid, 0)

    if cur < fine:
        return await interaction.response.send_message(
            "❌ 재화가 부족합니다.",
            ephemeral=True
        )

    # 💰 재화 차감
    money[uid] = cur - fine
    save_json(MONEY_FILE, money)

    # 🗑️ 벌금 데이터 삭제
    del fines[uid]
    save_json(FINE_FILE, fines)

    # 🏷️ 벌금 역할 제거 (확실하게)
    fine_role = discord.utils.get(interaction.guild.roles, name=FINE_ROLE)
    if fine_role and fine_role in member.roles:
        await member.remove_roles(fine_role)

    await interaction.response.send_message(
        f"✅ 벌금 {fine}원 납부 완료!\n"
        f"🏷️ 벌금대상 역할이 해제되었습니다.",
        ephemeral=True
    )

# =====================
# 🔹 월급 지급 (관리자)
# =====================
@client.tree.command(
    name="월급지급",
    description="국가 소속 인원에게 월급을 일괄 지급합니다. (관리자 전용)"
)
async def salary(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ 관리자 전용", ephemeral=True)

    today = str(datetime.date.today())
    log = load_json(SALARY_LOG)

    count = 0
    for m in interaction.guild.members:
        if m.bot:
            continue
        if PUNISH_ROLE in [r.name for r in m.roles]:
            continue

        uid = str(m.id)
        if log.get(uid) == today:
            continue

        pay = max([ROLE_SALARY.get(r.name, 0) for r in m.roles], default=0)
        if pay > 0:
            add_money(m.id, pay)
            log[uid] = today
            count += 1

    save_json(SALARY_LOG, log)
    await interaction.response.send_message(f"🏦 월급 지급 완료 ({count}명)")

# =====================
# 🚀 실행
# =====================
client.run(os.environ["DISCORD_TOKEN"])
