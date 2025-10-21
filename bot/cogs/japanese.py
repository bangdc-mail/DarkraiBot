# Plugin: Japanese
# Version: 1.0.0
# Author: DarkraiBot
# Description: Japanese learning tools - Translation and Kanji dictionary lookup
# Dependencies: googletrans, jamdict, requests
# Permissions: user

"""
Japanese Learning Cog - Tools for learning and using Japanese.

Features:
- Text translation between languages (focus on Japanese/English)
- Kanji dictionary lookup with readings, meanings, and examples
- Word pronunciation assistance
- Learning utilities for Japanese students
"""

import logging
import asyncio
from datetime import datetime
from typing import Optional, List, Dict

import discord
from discord.ext import commands
import aiohttp

from utils.permissions import user_level

logger = logging.getLogger(__name__)

try:
    from googletrans import Translator, LANGUAGES

    TRANSLATION_AVAILABLE = True
except ImportError:
    TRANSLATION_AVAILABLE = False
    logger.warning("googletrans not available - translation features disabled")

try:
    import jamdict

    JAMDICT_AVAILABLE = True
except ImportError:
    JAMDICT_AVAILABLE = False
    logger.warning("jamdict not available - kanji dictionary features disabled")


class JapaneseCog(commands.Cog):
    """Japanese learning tools and utilities."""

    def __init__(self, bot):
        self.bot = bot
        self.translator = None
        self.jam = None

        # Initialize translation service
        if TRANSLATION_AVAILABLE:
            try:
                self.translator = Translator()
                logger.info("Translation service initialized")
            except Exception as e:
                logger.error(f"Failed to initialize translator: {e}")

        # Initialize Jamdict for kanji lookup
        if JAMDICT_AVAILABLE:
            try:
                # Try to initialize jamdict with proper error handling
                import os

                # Check if jamdict database exists and is accessible
                try:
                    self.jam = jamdict.Jamdict()
                    # Test the database with a simple lookup
                    test_result = self.jam.lookup("水")
                    logger.info("Jamdict kanji dictionary initialized successfully")
                except Exception as db_error:
                    logger.warning(f"Jamdict database not accessible: {db_error}")
                    # Try to use jamdict-data package or provide fallback
                    try:
                        # Alternative initialization method
                        self.jam = jamdict.Jamdict(auto_expand=True)
                        logger.info("Jamdict initialized with auto-expand")
                    except Exception as fallback_error:
                        logger.error(
                            f"Failed to initialize jamdict with fallback: {fallback_error}"
                        )
                        self.jam = None

            except Exception as e:
                logger.error(f"Failed to initialize jamdict: {e}")
                self.jam = None

        # Common language codes for translation
        self.language_codes = {
            "japanese": "ja",
            "jp": "ja",
            "ja": "ja",
            "english": "en",
            "en": "en",
            "eng": "en",
            "korean": "ko",
            "ko": "ko",
            "kr": "ko",
            "chinese": "zh",
            "zh": "zh",
            "cn": "zh",
            "spanish": "es",
            "es": "es",
            "french": "fr",
            "fr": "fr",
            "german": "de",
            "de": "de",
            "auto": "auto",
        }

    async def fallback_kanji_lookup(self, query: str) -> dict:
        """
        Fallback kanji lookup using online API when local database is unavailable.
        """
        try:
            # Use a simple online kanji API as fallback
            async with aiohttp.ClientSession() as session:
                # Try jisho.org API (free and doesn't require API key)
                url = f"https://jisho.org/api/v1/search/words?keyword={query}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        return None
        except Exception as e:
            logger.error(f"Fallback kanji lookup error: {e}")
            return None

    @commands.group(
        name="translate", aliases=["tr", "trans"], invoke_without_command=True
    )
    @user_level()
    async def translate(
        self, ctx, from_lang: str = "auto", to_lang: str = "en", *, text: str
    ):
        """
        Translate text between languages.

        Usage:
        !translate <text> - Auto-detect to English
        !translate ja en <text> - Japanese to English
        !translate auto ja <text> - Auto-detect to Japanese
        !translate from_lang to_lang <text>

        Common language codes: ja (Japanese), en (English), ko (Korean),
        zh (Chinese), es (Spanish), fr (French), de (German)
        """
        if not TRANSLATION_AVAILABLE or not self.translator:
            embed = discord.Embed(
                title="❌ Translation Unavailable",
                description="Translation service is not available. Please contact the bot owner.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)
            return

        # Handle single argument case (just text, default auto->en)
        if to_lang and not text.strip():
            text = to_lang
            to_lang = "en"
            from_lang = "auto"

        # Normalize language codes
        from_lang = self.language_codes.get(from_lang.lower(), from_lang.lower())
        to_lang = self.language_codes.get(to_lang.lower(), to_lang.lower())

        if len(text) > 1000:
            await ctx.send("❌ Text too long! Please limit to 1000 characters.")
            return

        try:
            # Add typing indicator
            async with ctx.typing():
                # Perform translation
                result = await asyncio.to_thread(
                    self.translator.translate, text, src=from_lang, dest=to_lang
                )

                # Create embed
                embed = discord.Embed(
                    title="🌐 Translation",
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow(),
                )

                # Detect source language
                detected_lang = result.src
                detected_name = LANGUAGES.get(detected_lang, detected_lang).title()
                target_name = LANGUAGES.get(to_lang, to_lang).title()

                embed.add_field(
                    name=f"📝 Original ({detected_name})",
                    value=f"```{text[:500]}```",
                    inline=False,
                )

                embed.add_field(
                    name=f"🔄 Translation ({target_name})",
                    value=f"```{result.text[:500]}```",
                    inline=False,
                )

                # Add confidence if available
                if hasattr(result, "confidence") and result.confidence:
                    confidence = int(result.confidence * 100)
                    embed.add_field(
                        name="📊 Confidence", value=f"{confidence}%", inline=True
                    )

                embed.set_footer(text="Powered by Google Translate")
                await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Translation error: {e}")
            embed = discord.Embed(
                title="❌ Translation Error",
                description="Failed to translate the text. Please try again or contact support.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)

    @translate.command(name="languages", aliases=["langs", "list"])
    @user_level()
    async def translate_languages(self, ctx):
        """List supported language codes for translation."""
        if not TRANSLATION_AVAILABLE:
            await ctx.send("❌ Translation service not available.")
            return

        embed = discord.Embed(
            title="🌍 Supported Languages",
            description="Common language codes for translation:",
            color=discord.Color.blue(),
        )

        common_langs = [
            "🇯🇵 **ja** - Japanese",
            "🇺🇸 **en** - English",
            "🇰🇷 **ko** - Korean",
            "🇨🇳 **zh** - Chinese",
            "🇪🇸 **es** - Spanish",
            "🇫🇷 **fr** - French",
            "🇩🇪 **de** - German",
            "🔍 **auto** - Auto-detect",
        ]

        embed.add_field(
            name="Most Common", value="\n".join(common_langs[:4]), inline=True
        )

        embed.add_field(name="Others", value="\n".join(common_langs[4:]), inline=True)

        embed.add_field(
            name="Usage Examples",
            value="```!translate ja en こんにちは\n!translate auto ja Hello\n!translate こんにちは```",
            inline=False,
        )

        await ctx.send(embed=embed)

    @commands.group(name="kanji", aliases=["k"], invoke_without_command=True)
    @user_level()
    async def kanji(self, ctx, *, query: str):
        """
        Look up Kanji characters, words, or readings.

        Usage: !kanji 漢字
               !kanji water
               !kanji みず
        """
        if not JAMDICT_AVAILABLE or not self.jam:
            # Try fallback API method
            embed = discord.Embed(
                title="⚠️ Using Fallback Dictionary",
                description="Local dictionary unavailable, using online fallback...",
                color=discord.Color.orange(),
            )
            await ctx.send(embed=embed)

            try:
                async with ctx.typing():
                    fallback_data = await self.fallback_kanji_lookup(query)

                    if not fallback_data or not fallback_data.get("data"):
                        embed = discord.Embed(
                            title="❌ No Results Found",
                            description=f"No entries found for: `{query}`",
                            color=discord.Color.orange(),
                        )
                        await ctx.send(embed=embed)
                        return

                    # Process fallback data
                    for item in fallback_data["data"][:3]:  # Limit to 3 results
                        embed = discord.Embed(
                            title="📖 Dictionary Entry (Online)",
                            color=discord.Color.blue(),
                            timestamp=datetime.utcnow(),
                        )

                        # Japanese text
                        japanese_text = ""
                        if item.get("japanese"):
                            readings = []
                            for jp in item["japanese"][:3]:
                                if jp.get("word"):
                                    readings.append(jp["word"])
                                elif jp.get("reading"):
                                    readings.append(jp["reading"])
                            japanese_text = " • ".join(readings)

                        if japanese_text:
                            embed.add_field(
                                name="📝 Japanese", value=japanese_text, inline=True
                            )

                        # English meanings
                        if item.get("senses"):
                            meanings = []
                            for sense in item["senses"][:3]:
                                if sense.get("english_definitions"):
                                    meaning = "; ".join(
                                        sense["english_definitions"][:3]
                                    )
                                    if sense.get("parts_of_speech"):
                                        pos = ", ".join(sense["parts_of_speech"][:2])
                                        meaning = f"({pos}) {meaning}"
                                    meanings.append(meaning)

                            if meanings:
                                embed.add_field(
                                    name="💭 Meanings",
                                    value="\n".join(meanings),
                                    inline=False,
                                )

                        embed.set_footer(text="Powered by Jisho.org API")
                        await ctx.send(embed=embed)

                    return

            except Exception as e:
                logger.error(f"Fallback kanji lookup error: {e}")
                embed = discord.Embed(
                    title="❌ Dictionary Unavailable",
                    description=(
                        "Both local and online dictionary services are unavailable.\n\n"
                        "**Possible solutions:**\n"
                        "• Install jamdict-data: `pip install jamdict-data`\n"
                        "• Check internet connection\n"
                        "• Contact bot administrator"
                    ),
                    color=discord.Color.red(),
                )
                embed.add_field(
                    name="🔄 Alternative",
                    value="Try using `!translate` for basic Japanese text translation.",
                    inline=False,
                )
                await ctx.send(embed=embed)
                return

        if len(query) > 50:
            await ctx.send("❌ Query too long! Please limit to 50 characters.")
            return

        try:
            async with ctx.typing():
                # Search for entries
                result = self.jam.lookup(query)

                if not result.entries and not result.chars:
                    embed = discord.Embed(
                        title="❌ No Results Found",
                        description=f"No entries found for: `{query}`",
                        color=discord.Color.orange(),
                    )
                    await ctx.send(embed=embed)
                    return

                embeds = []

                # Process character entries (individual kanji)
                for char in result.chars[:3]:  # Limit to 3 characters
                    embed = discord.Embed(
                        title=f"📚 Kanji: {char.literal}",
                        color=discord.Color.green(),
                        timestamp=datetime.utcnow(),
                    )

                    # Add readings - handle different attribute names
                    try:
                        # Try different possible attribute names for on'yomi readings
                        on_readings = None
                        if hasattr(char, "on_readings") and char.on_readings:
                            on_readings = char.on_readings
                        elif hasattr(char, "on") and char.on:
                            on_readings = char.on
                        elif hasattr(char, "onyomi") and char.onyomi:
                            on_readings = char.onyomi

                        if on_readings:
                            embed.add_field(
                                name="🔊 On'yomi (音読み)",
                                value=" • ".join(str(r) for r in on_readings[:5]),
                                inline=True,
                            )
                    except Exception as e:
                        logger.debug(f"Error accessing on_readings: {e}")

                    try:
                        # Try different possible attribute names for kun'yomi readings
                        kun_readings = None
                        if hasattr(char, "kun_readings") and char.kun_readings:
                            kun_readings = char.kun_readings
                        elif hasattr(char, "kun") and char.kun:
                            kun_readings = char.kun
                        elif hasattr(char, "kunyomi") and char.kunyomi:
                            kun_readings = char.kunyomi

                        if kun_readings:
                            embed.add_field(
                                name="🔊 Kun'yomi (訓読み)",
                                value=" • ".join(str(r) for r in kun_readings[:5]),
                                inline=True,
                            )
                    except Exception as e:
                        logger.debug(f"Error accessing kun_readings: {e}")

                    # Add meanings - handle different attribute names
                    try:
                        meanings = None
                        if hasattr(char, "meanings") and char.meanings:
                            meanings = char.meanings
                        elif hasattr(char, "meaning") and char.meaning:
                            meanings = (
                                char.meaning
                                if isinstance(char.meaning, list)
                                else [char.meaning]
                            )
                        elif hasattr(char, "english") and char.english:
                            meanings = char.english

                        if meanings:
                            meanings_text = " • ".join(str(m) for m in meanings[:8])
                            embed.add_field(
                                name="💭 Meanings", value=meanings_text, inline=False
                            )
                    except Exception as e:
                        logger.debug(f"Error accessing meanings: {e}")

                    # Add stroke count and other info
                    try:
                        stroke_count = None
                        if hasattr(char, "stroke_count") and char.stroke_count:
                            stroke_count = char.stroke_count
                        elif hasattr(char, "strokes") and char.strokes:
                            stroke_count = char.strokes
                        elif hasattr(char, "stroke") and char.stroke:
                            stroke_count = char.stroke

                        if stroke_count:
                            embed.add_field(
                                name="✏️ Strokes", value=str(stroke_count), inline=True
                            )
                    except Exception as e:
                        logger.debug(f"Error accessing stroke_count: {e}")

                    embeds.append(embed)

                # Process word entries
                for entry in result.entries[:3]:  # Limit to 3 entries
                    if entry.kanji_forms:
                        kanji_text = " • ".join([k.text for k in entry.kanji_forms[:3]])
                    else:
                        kanji_text = "N/A"

                    if entry.kana_forms:
                        kana_text = " • ".join([k.text for k in entry.kana_forms[:3]])
                    else:
                        kana_text = "N/A"

                    embed = discord.Embed(
                        title=f"📖 Word Entry",
                        color=discord.Color.blue(),
                        timestamp=datetime.utcnow(),
                    )

                    embed.add_field(name="📝 Kanji", value=kanji_text, inline=True)

                    embed.add_field(name="🔤 Reading", value=kana_text, inline=True)

                    # Add meanings
                    meanings = []
                    for sense in entry.senses[:3]:
                        if sense.glosses:
                            meaning = "; ".join(sense.glosses[:3])
                            if sense.pos:
                                pos_text = ", ".join(sense.pos[:2])
                                meaning = f"({pos_text}) {meaning}"
                            meanings.append(meaning)

                    if meanings:
                        embed.add_field(
                            name="💭 Definitions",
                            value="\n".join(meanings),
                            inline=False,
                        )

                    embeds.append(embed)

                # Send results
                if embeds:
                    for embed in embeds:
                        embed.set_footer(text="Powered by JMdict/KANJIDIC")
                        await ctx.send(embed=embed)
                else:
                    await ctx.send("❌ No detailed information found for the query.")

        except Exception as e:
            logger.error(f"Kanji lookup error: {e}")
            embed = discord.Embed(
                title="❌ Lookup Error",
                description="Failed to perform kanji lookup. Please try again.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)

    @kanji.command(name="random", aliases=["rand"])
    @user_level()
    async def kanji_random(self, ctx):
        """Get a random kanji character for study."""
        if not JAMDICT_AVAILABLE or not self.jam:
            await ctx.send("❌ Kanji dictionary not available.")
            return

        try:
            # Get a random character (this is a simplified implementation)
            # In practice, you might want to maintain a list of common kanji
            import random

            # Common kanji for beginners
            common_kanji = [
                "水",
                "火",
                "土",
                "木",
                "金",
                "日",
                "月",
                "人",
                "大",
                "小",
                "中",
                "学",
                "校",
                "本",
                "車",
                "家",
                "国",
                "食",
                "飲",
                "見",
            ]

            random_kanji = random.choice(common_kanji)

            # Look up the selected kanji
            result = self.jam.lookup(random_kanji)

            if result.chars:
                char = result.chars[0]
                embed = discord.Embed(
                    title=f"🎲 Random Kanji: {char.literal}",
                    color=discord.Color.purple(),
                    timestamp=datetime.utcnow(),
                )

                # Use the same robust attribute access as the main kanji command
                try:
                    # Try different possible attribute names for on'yomi readings
                    on_readings = None
                    if hasattr(char, "on_readings") and char.on_readings:
                        on_readings = char.on_readings
                    elif hasattr(char, "on") and char.on:
                        on_readings = char.on
                    elif hasattr(char, "onyomi") and char.onyomi:
                        on_readings = char.onyomi

                    if on_readings:
                        embed.add_field(
                            name="🔊 On'yomi",
                            value=" • ".join(str(r) for r in on_readings[:3]),
                            inline=True,
                        )
                except Exception as e:
                    logger.debug(f"Error accessing on_readings in random: {e}")

                try:
                    # Try different possible attribute names for kun'yomi readings
                    kun_readings = None
                    if hasattr(char, "kun_readings") and char.kun_readings:
                        kun_readings = char.kun_readings
                    elif hasattr(char, "kun") and char.kun:
                        kun_readings = char.kun
                    elif hasattr(char, "kunyomi") and char.kunyomi:
                        kun_readings = char.kunyomi

                    if kun_readings:
                        embed.add_field(
                            name="🔊 Kun'yomi",
                            value=" • ".join(str(r) for r in kun_readings[:3]),
                            inline=True,
                        )
                except Exception as e:
                    logger.debug(f"Error accessing kun_readings in random: {e}")

                try:
                    # Try different possible attribute names for meanings
                    meanings = None
                    if hasattr(char, "meanings") and char.meanings:
                        meanings = char.meanings
                    elif hasattr(char, "meaning") and char.meaning:
                        meanings = (
                            char.meaning
                            if isinstance(char.meaning, list)
                            else [char.meaning]
                        )
                    elif hasattr(char, "english") and char.english:
                        meanings = char.english

                    if meanings:
                        embed.add_field(
                            name="💭 Meanings",
                            value=" • ".join(str(m) for m in meanings[:5]),
                            inline=False,
                        )
                except Exception as e:
                    logger.debug(f"Error accessing meanings in random: {e}")

                embed.set_footer(text="Use !kanji <character> for more details")
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Could not find information for the random kanji.")

        except Exception as e:
            logger.error(f"Random kanji error: {e}")
            await ctx.send("❌ Error getting random kanji.")

    @commands.command(name="romaji", aliases=["rom"])
    @user_level()
    async def romaji(self, ctx, *, japanese_text: str):
        """
        Convert Japanese text to Romaji (experimental).

        Usage: !romaji こんにちは
        """
        # This is a basic implementation - for production use, consider libraries like pykakasi
        basic_hiragana = {
            "あ": "a",
            "い": "i",
            "う": "u",
            "え": "e",
            "お": "o",
            "か": "ka",
            "き": "ki",
            "く": "ku",
            "け": "ke",
            "こ": "ko",
            "が": "ga",
            "ぎ": "gi",
            "ぐ": "gu",
            "げ": "ge",
            "ご": "go",
            "さ": "sa",
            "し": "shi",
            "す": "su",
            "せ": "se",
            "そ": "so",
            "ざ": "za",
            "じ": "ji",
            "ず": "zu",
            "ぜ": "ze",
            "ぞ": "zo",
            "た": "ta",
            "ち": "chi",
            "つ": "tsu",
            "て": "te",
            "と": "to",
            "だ": "da",
            "ぢ": "ji",
            "づ": "zu",
            "で": "de",
            "ど": "do",
            "な": "na",
            "に": "ni",
            "ぬ": "nu",
            "ね": "ne",
            "の": "no",
            "は": "ha",
            "ひ": "hi",
            "ふ": "fu",
            "へ": "he",
            "ほ": "ho",
            "ば": "ba",
            "び": "bi",
            "ぶ": "bu",
            "べ": "be",
            "ぼ": "bo",
            "ぱ": "pa",
            "ぴ": "pi",
            "ぷ": "pu",
            "ぺ": "pe",
            "ぽ": "po",
            "ま": "ma",
            "み": "mi",
            "む": "mu",
            "め": "me",
            "も": "mo",
            "や": "ya",
            "ゆ": "yu",
            "よ": "yo",
            "ら": "ra",
            "り": "ri",
            "る": "ru",
            "れ": "re",
            "ろ": "ro",
            "わ": "wa",
            "ゐ": "wi",
            "ゑ": "we",
            "を": "wo",
            "ん": "n",
        }

        if len(japanese_text) > 100:
            await ctx.send("❌ Text too long! Please limit to 100 characters.")
            return

        try:
            romaji_result = ""
            for char in japanese_text:
                if char in basic_hiragana:
                    romaji_result += basic_hiragana[char]
                elif char in "、。！？":
                    romaji_result += char
                elif char == " ":
                    romaji_result += " "
                else:
                    romaji_result += char  # Keep unknown characters as-is

            embed = discord.Embed(
                title="🔤 Romaji Conversion",
                color=discord.Color.green(),
                timestamp=datetime.utcnow(),
            )

            embed.add_field(
                name="📝 Original", value=f"```{japanese_text}```", inline=False
            )

            embed.add_field(
                name="🔤 Romaji", value=f"```{romaji_result}```", inline=False
            )

            embed.set_footer(text="Basic hiragana conversion - Limited functionality")
            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Romaji conversion error: {e}")
            await ctx.send("❌ Error converting to romaji.")

    @commands.command(name="jpdebug", hidden=True)
    @user_level()
    async def japanese_debug(self, ctx, *, query: str = "水"):
        """Debug command to inspect jamdict Character object structure."""
        if not JAMDICT_AVAILABLE or not self.jam:
            await ctx.send("❌ Jamdict not available for debugging.")
            return

        try:
            result = self.jam.lookup(query)

            if result.chars:
                char = result.chars[0]

                # Get all attributes of the Character object
                attributes = [attr for attr in dir(char) if not attr.startswith("_")]

                embed = discord.Embed(
                    title=f"🔍 Debug: Character Object for '{char.literal}'",
                    color=discord.Color.orange(),
                    timestamp=datetime.utcnow(),
                )

                # Show available attributes
                embed.add_field(
                    name="📋 Available Attributes",
                    value=f"```{', '.join(attributes[:20])}```",
                    inline=False,
                )

                # Try to access and show reading-related attributes
                reading_info = []
                for attr in [
                    "on_readings",
                    "kun_readings",
                    "on",
                    "kun",
                    "onyomi",
                    "kunyomi",
                ]:
                    if hasattr(char, attr):
                        try:
                            value = getattr(char, attr)
                            reading_info.append(
                                f"{attr}: {type(value).__name__} = {value}"
                            )
                        except Exception as e:
                            reading_info.append(f"{attr}: Error = {e}")

                if reading_info:
                    embed.add_field(
                        name="📖 Reading Attributes",
                        value=f"```{chr(10).join(reading_info[:5])}```",
                        inline=False,
                    )

                # Try to access meaning-related attributes
                meaning_info = []
                for attr in ["meanings", "meaning", "english"]:
                    if hasattr(char, attr):
                        try:
                            value = getattr(char, attr)
                            meaning_info.append(
                                f"{attr}: {type(value).__name__} = {value}"
                            )
                        except Exception as e:
                            meaning_info.append(f"{attr}: Error = {e}")

                if meaning_info:
                    embed.add_field(
                        name="💭 Meaning Attributes",
                        value=f"```{chr(10).join(meaning_info[:5])}```",
                        inline=False,
                    )

                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ No character found for: {query}")

        except Exception as e:
            await ctx.send(f"❌ Debug error: {e}")

    @commands.command(name="jpstatus", aliases=["japanese-status"])
    @user_level()
    async def japanese_status(self, ctx):
        """Check the status of Japanese learning services."""
        embed = discord.Embed(
            title="🇯🇵 Japanese Learning Services Status",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow(),
        )

        # Translation service status
        if TRANSLATION_AVAILABLE and self.translator:
            embed.add_field(
                name="🌐 Translation Service",
                value="✅ Available (Google Translate)",
                inline=True,
            )
        else:
            embed.add_field(
                name="🌐 Translation Service", value="❌ Unavailable", inline=True
            )

        # Kanji dictionary status
        if JAMDICT_AVAILABLE and self.jam:
            embed.add_field(
                name="📚 Kanji Dictionary",
                value="✅ Available (Local Database)",
                inline=True,
            )
        elif JAMDICT_AVAILABLE:
            embed.add_field(
                name="📚 Kanji Dictionary",
                value="⚠️ Fallback Mode (Online API)",
                inline=True,
            )
        else:
            embed.add_field(
                name="📚 Kanji Dictionary", value="❌ Unavailable", inline=True
            )

        # Romaji conversion
        embed.add_field(
            name="🔤 Romaji Conversion", value="✅ Available (Basic)", inline=True
        )

        # Available commands
        available_commands = []
        if TRANSLATION_AVAILABLE and self.translator:
            available_commands.append("`!translate` - Text translation")
        if JAMDICT_AVAILABLE:
            available_commands.append("`!kanji` - Dictionary lookup")
        available_commands.append("`!romaji` - Hiragana conversion")

        if available_commands:
            embed.add_field(
                name="📋 Available Commands",
                value="\n".join(available_commands),
                inline=False,
            )

        # Installation help
        missing_services = []
        if not TRANSLATION_AVAILABLE:
            missing_services.append("googletrans")
        if not JAMDICT_AVAILABLE:
            missing_services.append("jamdict")

        if missing_services:
            embed.add_field(
                name="🔧 Installation Help",
                value=f"Missing: `pip install {' '.join(missing_services)}`",
                inline=False,
            )

        await ctx.send(embed=embed)


async def setup(bot):
    """Setup function to add the JapaneseCog to the bot."""
    await bot.add_cog(JapaneseCog(bot))
    logger.info("Japanese learning cog loaded successfully")
