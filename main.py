import discord, json, requests
from discord.ext import commands
from discord import app_commands

config = json.load(open('config.json', encoding='utf-8'))
bot = commands.Bot(command_prefix='?', intents=discord.Intents.all())

key = config['api-key']
token = config['bot-token']

@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
        print(f'Logged in as {bot.user}')
    except Exception as error:
        print(error)
        return

@bot.tree.command(name='shop-info', description='Get info about your sellix shop')
async def info(interaction: discord.Interaction):
    if interaction.user.guild_permissions.administrator is False:
        await interaction.response.send_message('You are not allowed to use this command', ephemeral=True)
        return
    
    url = 'https://dev.sellix.io/v1/self'
    headers = {'Authorization': key}
    r = requests.request('GET', url, headers=headers)

    if r.status_code == 200:
        data = r.json()
        name = data.get('data', {}).get('name', {})
        tos = data.get('data', {}).get('terms_of_service', {})
        dc = data.get('data', {}).get('discord_link', {})
        plan = data.get('data', {}).get('type', {})


        embed = discord.Embed(
            title=f'__{name}__',
            color=discord.Color.blurple()
        )
        embed.add_field(name='Tos:', value=tos, inline=False)
        embed.add_field(name='Discord:', value=dc, inline=False)
        embed.add_field(name='Plan:', value=plan)
        embed.set_thumbnail(url=interaction.guild.icon.url)
        embed.set_footer(text=interaction.guild.name, icon_url=interaction.guild.icon.url)

        await interaction.response.send_message(embed=embed)
    elif r.status_code == 401:
        await interaction.response.send_message('Invalid api key', ephemeral=True)

@bot.tree.command(name='get-order', description='Get information about a specific order id')
@app_commands.describe(orderid="Enter the id of the order you want to track")
async def orderinfo(interaction: discord.Interaction, orderid: str):
    try:
        if interaction.user.guild_permissions.administrator is False:
            await interaction.response.send_message('You are not allowed to use this command', ephemeral=True)
            return
    
        url = f'https://dev.sellix.io/v1/orders/{orderid}' 
        headers = {'Authorization': key}
        r = requests.request('GET', url, headers=headers)

        if r.status_code == 200:
            data = r.json()
            product = data.get('data', {}).get('order', {}).get('product_title')
            total = data.get('data', {}).get('order', {}).get('total', {})
            status = data.get('data', {}).get('order', {}).get('status', {})
            if 'PENDING' in status:
                status = 'Awaiting payment...'
            elif 'COMPLETED' in status:
                status = 'Payment received'

            embed = discord.Embed(
                title="__Order Info__",
                description=f"{orderid} order info.",
                color=discord.Color.blurple()
            )
            embed.add_field(name="Product:", value=product, inline=False)
            embed.add_field(name="Price:", value=total, inline=False)
            embed.add_field(name="Status:", value=status, inline=False)
            embed.set_thumbnail(url=interaction.guild.icon.url)
            embed.set_footer(icon_url=interaction.guild.icon.url, text=interaction.guild.name)

            await interaction.response.send_message(embed=embed)
        elif r.status_code == 401:
            await interaction.response.send_message("Invalid api key", ephemeral=True)
    except AttributeError:
        await interaction.response.send_message("Please enter a valid order id.")

@bot.tree.command(name="create-coupon", description="Create a coupon for your webshop")
@app_commands.describe(name="Name of your coupon code", discount="Discount in %'s")
async def create_coupon(interaction: discord.Interaction, name: str, discount: int):
    try:
        if interaction.user.guild_permissions.administrator is False:
            await interaction.response.send_message("You are not allowed to use this command", ephemeral=True)
            return
        
        url = "https://dev.sellix.io/v1/coupons"
        headers = {
            "Authorization": key,
            "Content-Type": "application/json"
        }
        payload = {
                "code": name,
                "discount_value": discount,
                "max_uses": '',
                "discount_type": "PERCENTAGE",
                "disabled_with_volume_discounts": True,
                "all_recurring_bill_invoices": True,
                "expire_at": None,
                "products_bound": 'any'
            }  
        r = requests.request("POST", url, json=payload, headers=headers)
        embed = discord.Embed(description=f"New coupon created; {name} / {discount}% | Use the /delete-coupon command to delete the coupon", color=discord.Color.blurple())
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(e)


@bot.tree.command(name="coupon-list", description="Get a list of all coupons")
async def listcpns(interaction: discord.Interaction):
    url = "https://dev.sellix.io/v1/coupons"
    headers = {"Authorization": key}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        coupons_data = r.json().get("data", {}).get("coupons", [])
        if coupons_data:
            embed = discord.Embed(
                title="__Coupon Codes__",
                description="A list of all of your active & inactive coupon codes.",
                color=discord.Color.blurple()
            )
            cpn = 1
            for coupon in coupons_data:
                cpn_name = coupon.get("code")
                cpn_discount = coupon.get("discount")
                cpn_expiry = coupon.get("expire_at")
                embed.add_field(name=f"Coupon {cpn}:", value=f"Code: __{cpn_name}__\nDiscount: {cpn_discount}%\nExpires at: {cpn_expiry}", inline=False)
                cpn += 1
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("No exisiting coupons found.", ephemeral=True)
    elif r.status_code == 401:
        await interaction.response.send_message("Invalid api key", ephemeral=True)


bot.run(token)
