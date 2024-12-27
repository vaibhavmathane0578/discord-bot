import discord
from discord.ext import commands
import pandas as pd
import os

# Discord Bot Setup
intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix="/", intents=intents)

# Store uploaded CSVs in memory (temporary storage)
uploaded_files = {}

# Helper function to read CSV from file
def read_csv(file_path):
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        return None

# Command to upload CSV file
@bot.command()
async def upload(ctx):
    """Command to upload CSV file."""
    await ctx.send("Please upload your CSV file for processing.")

# Event: Detect file upload
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Check if the message contains attachments (CSV files)
    if message.attachments:
        for attachment in message.attachments:
            if attachment.filename.endswith('.csv'):
                file_path = f"temp/{attachment.filename}"
                
                # Download the file
                await attachment.save(file_path)
                
                # Read the CSV and store it for future use
                df = read_csv(file_path)
                
                if df is not None:
                    # Store the data with a reference to the user
                    uploaded_files[message.author.id] = {"filename": attachment.filename, "data": df}
                    await message.channel.send(f"CSV file `{attachment.filename}` uploaded and processed successfully!")
                else:
                    await message.channel.send("Failed to process the CSV file. Please make sure it's in the correct format.")
                
                # Clean up the file after processing
                os.remove(file_path)

    await bot.process_commands(message)

# Command to view all uploaded CSV files (for the DM)
@bot.command()
async def files(ctx):
    """Command to list all uploaded CSV files."""
    if ctx.author.id in uploaded_files:
        file_info = uploaded_files[ctx.author.id]
        await ctx.send(f"Uploaded CSV File: `{file_info['filename']}`")
    else:
        await ctx.send("You haven't uploaded any CSV files yet.")

# Command to search through CSV data
@bot.command()
async def find(ctx, *, query):
    """Command to find entries based on column and value."""
    if ctx.author.id not in uploaded_files:
        await ctx.send("Please upload a CSV file first using `/upload`.")
        return

    file_info = uploaded_files[ctx.author.id]
    df = file_info["data"]

    # Parsing the command query (assumes column:value format)
    try:
        column, value = query.split(":")
        column = column.strip()
        value = value.strip()

        if column not in df.columns:
            await ctx.send(f"Column `{column}` not found in the CSV file.")
            return

        # Filter the data
        filtered_data = df[df[column].str.contains(value, case=False, na=False)]

        if filtered_data.empty:
            await ctx.send(f"No results found for `{column}: {value}`.")
            return

        # Display results
        response = f"**Results for `{column}: {value}`** in `{file_info['filename']}`:\n"
        for _, row in filtered_data.iterrows():
            formatted_row = "\n".join([f"**{key}:** {val}" for key, val in row.items()])
            response += f"\n{formatted_row}\n{'-'*40}"

        for chunk in [response[i:i+2000] for i in range(0, len(response), 2000)]:
            await ctx.send(chunk)
    
    except ValueError:
        await ctx.send("Invalid query format. Use `column:value` (e.g., `Shop Name:Blacksmith`).")

# Command to clear uploaded CSV files
@bot.command()
async def clear(ctx):
    """Command to clear the uploaded CSV files."""
    if ctx.author.id in uploaded_files:
        del uploaded_files[ctx.author.id]
        await ctx.send("Your uploaded CSV files have been cleared.")
    else:
        await ctx.send("You haven't uploaded any CSV files yet.")

# Help Command
@bot.command()
async def help(ctx):
    help_text = """
    **Available Commands:**
    - `/upload` - Upload your CSV file for processing.
    - `/files` - View uploaded CSV files.
    - `/find column:value` - Search for data in the uploaded CSV (e.g., `/find Shop Name:Blacksmith`).
    - `/clear` - Clear your uploaded CSV files.
    - `/help` - Display this help message.
    """
    await ctx.send(help_text)

# Run the Bot
bot.run("")

