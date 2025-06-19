import aiohttp
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
from app.core.config import settings
from app.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class SportsAPIService:
    """Serviço base para APIs de esportes"""
    
    def __init__(self):
        self.session = None
    
    async def get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        if self.session:
            await self.session.close()

class FootballAPI(SportsAPIService):
    """Integração com API-Football"""
    
    BASE_URL = "https://v3.football.api-sports.io"
    
    async def get_fixtures(self, date: str = None) -> List[Dict]:
        """Busca partidas de futebol"""
        if not settings.API_FOOTBALL_KEY:
            logger.warning("API Football key não configurada")
            return []
        
        cache_key = f"football_fixtures_{date or 'today'}"
        cached = await cache.get(cache_key)
        if cached:
            return cached
        
        try:
            session = await self.get_session()
            url = f"{self.BASE_URL}/fixtures"
            
            params = {
                "date": date or datetime.now().strftime("%Y-%m-%d"),
                "status": "NS-1H-HT-2H-ET-P-FT"
            }
            
            headers = {
                "x-rapidapi-key": settings.API_FOOTBALL_KEY,
                "x-rapidapi-host": "v3.football.api-sports.io"
            }
            
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    fixtures = self._format_fixtures(data.get("response", []))
                    await cache.set(cache_key, fixtures, expire=1800)  # 30 min
                    return fixtures
                else:
                    logger.error(f"Erro API Football: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Erro ao buscar fixtures de futebol: {e}")
            return []
    
    async def get_team_stats(self, team_id: int, season: int) -> Dict:
        """Busca estatísticas de um time"""
        cache_key = f"football_team_{team_id}_{season}"
        cached = await cache.get(cache_key)
        if cached:
            return cached
        
        try:
            session = await self.get_session()
            url = f"{self.BASE_URL}/teams/statistics"
            
            params = {"team": team_id, "season": season, "league": 39}  # Premier League
            headers = {
                "x-rapidapi-key": settings.API_FOOTBALL_KEY,
                "x-rapidapi-host": "v3.football.api-sports.io"
            }
            
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    stats = self._format_team_stats(data.get("response", {}))
                    await cache.set(cache_key, stats, expire=3600)  # 1 hora
                    return stats
                    
        except Exception as e:
            logger.error(f"Erro ao buscar stats do time: {e}")
            
        return {}
    
    def _format_fixtures(self, fixtures: List[Dict]) -> List[Dict]:
        """Formata dados das partidas"""
        formatted = []
        for fixture in fixtures:
            try:
                formatted.append({
                    "id": fixture["fixture"]["id"],
                    "date": fixture["fixture"]["date"],
                    "status": fixture["fixture"]["status"]["short"],
                    "league": fixture["league"]["name"],
                    "season": fixture["league"]["season"],
                    "home_team": fixture["teams"]["home"]["name"],
                    "away_team": fixture["teams"]["away"]["name"],
                    "home_team_id": fixture["teams"]["home"]["id"],
                    "away_team_id": fixture["teams"]["away"]["id"],
                    "sport": "football"
                })
            except KeyError as e:
                logger.warning(f"Fixture mal formatado: {e}")
                continue
        return formatted
    
    def _format_team_stats(self, stats: Dict) -> Dict:
        """Formata estatísticas do time"""
        try:
            goals = stats.get("goals", {})
            return {
                "goals_for_avg": goals.get("for", {}).get("average", {}).get("total", 0),
                "goals_against_avg": goals.get("against", {}).get("average", {}).get("total", 0),
                "home_goals_avg": goals.get("for", {}).get("average", {}).get("home", 0),
                "away_goals_avg": goals.get("for", {}).get("average", {}).get("away", 0),
                "form": stats.get("form", ""),
                "wins": stats.get("fixtures", {}).get("wins", {}).get("total", 0),
                "draws": stats.get("fixtures", {}).get("draws", {}).get("total", 0),
                "losses": stats.get("fixtures", {}).get("loses", {}).get("total", 0)
            }
        except Exception:
            return {}

class PandaScoreAPI(SportsAPIService):
    """Integração com PandaScore para e-sports"""
    
    BASE_URL = "https://api.pandascore.co"
    
    async def get_matches(self, game: str = "csgo") -> List[Dict]:
        """Busca partidas de e-sports"""
        if not settings.PANDASCORE_KEY:
            logger.warning("PandaScore key não configurada")
            return []
        
        cache_key = f"esports_{game}_matches"
        cached = await cache.get(cache_key)
        if cached:
            return cached
        
        try:
            session = await self.get_session()
            url = f"{self.BASE_URL}/{game}/matches"
            
            params = {
                "filter[status]": "not_started,running",
                "sort": "begin_at",
                "page[size]": 50
            }
            
            headers = {"Authorization": f"Bearer {settings.PANDASCORE_KEY}"}
            
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    matches = self._format_esports_matches(data, game)
                    await cache.set(cache_key, matches, expire=1800)
                    return matches
                    
        except Exception as e:
            logger.error(f"Erro ao buscar matches de {game}: {e}")
            
        return []
    
    def _format_esports_matches(self, matches: List[Dict], game: str) -> List[Dict]:
        """Formata partidas de e-sports"""
        formatted = []
        for match in matches:
            try:
                if not match.get("opponents") or len(match["opponents"]) < 2:
                    continue
                    
                formatted.append({
                    "id": match["id"],
                    "date": match["begin_at"],
                    "status": match["status"],
                    "league": match.get("league", {}).get("name", ""),
                    "tournament": match.get("tournament", {}).get("name", ""),
                    "home_team": match["opponents"][0]["opponent"]["name"],
                    "away_team": match["opponents"][1]["opponent"]["name"],
                    "home_team_id": match["opponents"][0]["opponent"]["id"],
                    "away_team_id": match["opponents"][1]["opponent"]["id"],
                    "best_of": match.get("number_of_games", 1),
                    "sport": game
                })
            except (KeyError, IndexError) as e:
                logger.warning(f"Match mal formatado: {e}")
                continue
        return formatted

class OddsAPI(SportsAPIService):
    """Integração com The Odds API"""
    
    BASE_URL = "https://api.the-odds-api.com/v4/sports"
    
    async def get_odds(self, sport: str = "soccer_epl") -> List[Dict]:
        """Busca odds de apostas"""
        if not settings.ODDS_API_KEY:
            logger.warning("Odds API key não configurada")
            return []
        
        cache_key = f"odds_{sport}"
        cached = await cache.get(cache_key)
        if cached:
            return cached
        
        try:
            session = await self.get_session()
            url = f"{self.BASE_URL}/{sport}/odds"
            
            params = {
                "apiKey": settings.ODDS_API_KEY,
                "regions": "uk,us,au",
                "markets": "h2h,spreads,totals",
                "oddsFormat": "decimal"
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    odds = self._format_odds(data)
                    await cache.set(cache_key, odds, expire=600)  # 10 min
                    return odds
                    
        except Exception as e:
            logger.error(f"Erro ao buscar odds: {e}")
            
        return []
    
    def _format_odds(self, odds_data: List[Dict]) -> List[Dict]:
        """Formata dados de odds"""
        formatted = []
        for event in odds_data:
            try:
                for bookmaker in event.get("bookmakers", []):
                    for market in bookmaker.get("markets", []):
                        formatted.append({
                            "event_id": event["id"],
                            "home_team": event["home_team"],
                            "away_team": event["away_team"],
                            "commence_time": event["commence_time"],
                            "bookmaker": bookmaker["title"],
                            "market": market["key"],
                            "outcomes": {
                                outcome["name"]: outcome["price"] 
                                for outcome in market.get("outcomes", [])
                            }
                        })
            except KeyError as e:
                logger.warning(f"Odds mal formatadas: {e}")
                continue
        return formatted

# Instâncias globais
football_api = FootballAPI()
pandascore_api = PandaScoreAPI()
odds_api = OddsAPI() 