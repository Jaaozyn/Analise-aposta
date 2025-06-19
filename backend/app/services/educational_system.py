"""
Educational System - Sistema de Conteúdo Educacional
Ensina usuários como interpretar e usar as análises da plataforma
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class LessonLevel(Enum):
    """Níveis de dificuldade das lições"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class LessonType(Enum):
    """Tipos de conteúdo educacional"""
    TEXT = "text"
    VIDEO = "video"
    INTERACTIVE = "interactive"
    QUIZ = "quiz"
    CASE_STUDY = "case_study"

@dataclass
class Lesson:
    """Estrutura de uma lição"""
    id: str
    title: str
    description: str
    content: str
    level: LessonLevel
    type: LessonType
    duration_minutes: int
    prerequisites: List[str]
    learning_objectives: List[str]
    practical_examples: List[Dict]
    quiz_questions: Optional[List[Dict]]
    completion_reward: int  # XP points

@dataclass
class UserProgress:
    """Progresso do usuário no sistema educacional"""
    user_id: str
    completed_lessons: List[str]
    current_level: LessonLevel
    total_xp: int
    certificates_earned: List[str]
    last_activity: datetime

class EducationalSystem:
    """Sistema de educação e treinamento"""
    
    def __init__(self):
        self.lessons = self._initialize_lessons()
    
    def _initialize_lessons(self) -> List[Lesson]:
        """Inicializa banco de lições"""
        
        return [
            # MÓDULO 1: FUNDAMENTOS
            Lesson(
                id="fundamentals_001",
                title="🎯 O que é Expected Value (EV+)?",
                description="Aprenda o conceito fundamental que guia todas nossas recomendações",
                content="""
# 🎯 Expected Value (EV+) - O Santo Graal das Apostas

## O que é Expected Value?

O **Expected Value (EV)** é a vantagem matemática que você tem sobre a casa de apostas em uma aposta específica. É a diferença entre a **probabilidade real** de um evento acontecer e a **probabilidade implícita** nas odds oferecidas.

## Fórmula do EV

```
EV = (Probabilidade Real × Odds) - 1
```

**Exemplo Prático:**
- **Jogo**: Real Madrid vs Barcelona
- **Aposta**: Over 2.5 Goals
- **Odds oferecidas**: 1.75 (57% de probabilidade implícita)
- **Nossa análise**: 68% de chance real

```
EV = (0.68 × 1.75) - 1 = 0.19 = +19% 🔥
```

## Por que EV+ é importante?

- ✅ **Lucro a longo prazo**: Apostas com EV+ são matematicamente vantajosas
- ✅ **Decisões objetivas**: Remove emoção da equação
- ✅ **Gestão de risco**: Foca apenas em oportunidades reais

## Na Prática

Quando você vê um pick com **EV+ de 12%**, significa que:
- A cada 100 apostas similares, você lucraria 12% em média
- É uma vantagem real sobre o mercado
- Vale a pena apostar (respeitando gestão de banca)

## ⚠️ Importante

- EV+ não garante vitória individual
- Foque no longo prazo (50+ apostas)
- Nunca aposte sem EV+ positivo

## Próximos Passos

1. Entenda como calculamos probabilidades
2. Aprenda sobre confidence score
3. Domine gestão de banca
                """,
                level=LessonLevel.BEGINNER,
                type=LessonType.TEXT,
                duration_minutes=15,
                prerequisites=[],
                learning_objectives=[
                    "Entender o conceito de Expected Value",
                    "Saber calcular EV básico",
                    "Reconhecer importância do EV+ nas apostas"
                ],
                practical_examples=[
                    {
                        "scenario": "Real Madrid (casa) vs Barcelona",
                        "odds": 2.10,
                        "real_probability": 0.55,
                        "ev_calculation": "(0.55 × 2.10) - 1 = +15.5%",
                        "recommendation": "APOSTAR - EV+ excelente"
                    }
                ],
                quiz_questions=[
                    {
                        "question": "Se um pick tem 60% de chance real e odds 1.80, qual o EV?",
                        "options": ["+8%", "-12%", "+5%", "0%"],
                        "correct": 0,
                        "explanation": "EV = (0.60 × 1.80) - 1 = +8%"
                    }
                ],
                completion_reward=100
            ),
            
            Lesson(
                id="fundamentals_002", 
                title="📊 Como Interpretamos Estatísticas",
                description="Entenda como transformamos dados em insights valiosos",
                content="""
# 📊 Como o QuantumBet Analisa Estatísticas

## Dados que Coletamos

### ⚽ Futebol
- **Média de gols** (últimos 10 jogos)
- **xG (Expected Goals)** - qualidade das finalizações
- **Posse de bola** e eficiência
- **Defesa**: gols sofridos, clean sheets
- **Forma atual**: últimos 5 resultados
- **Confrontos diretos** (H2H)
- **Fatores externos**: lesões, clima, importância do jogo

### 🏀 Basquete
- **Pontos por jogo** (ofensivo/defensivo)
- **Pace**: velocidade do jogo
- **Efficiency**: pontos por posse
- **Rebotes** e assistências
- **Performance em casa/fora**

## Como Interpretamos

### 1. Contexto é Tudo
- ❌ **Errado**: "Time X marca 2.5 gols/jogo"
- ✅ **Correto**: "Time X marca 2.5 gols/jogo CONTRA defesas similares ao adversário"

### 2. Ajustes por Qualidade
```
Gols Esperados = (Ataque Time A / Defesa Time B) × Fator Casa × Forma
```

### 3. Peso Temporal
- Jogos recentes: peso 3x
- Jogos médios: peso 2x  
- Jogos antigos: peso 1x

## Exemplo Prático: Real Madrid vs Atlético

### Dados Brutos
- **Real**: 2.1 gols/jogo em casa
- **Atlético**: 0.8 gols sofridos/jogo fora
- **H2H**: 2.3 gols/jogo (média últimos 5)

### Nossa Análise
1. **Ajuste defensivo**: Atlético tem defesa forte (-20%)
2. **Fator casa**: Real em casa (+15%)
3. **Forma atual**: Real em boa fase (+10%)
4. **Importância**: Derby (-5% imprevisibilidade)

### Resultado
```
Gols Esperados Real = 2.1 × 0.8 × 1.15 × 1.10 × 0.95 = 1.97 gols
```

## Indicadores-Chave

### 🎯 Força Ofensiva
- Gols/jogo vs qualidade das defesas enfrentadas
- xG/jogo (qualidade das chances)
- Finalizações por jogo

### 🛡️ Força Defensiva  
- Gols sofridos vs qualidade dos ataques enfrentados
- xG concedido
- Clean sheets %

### 📈 Forma Atual
- Últimos 5 jogos (peso maior)
- Performance em casa/fora
- Sequências de vitórias/derrotas

## ⚠️ Armadilhas Comuns

### 1. Números Enganosos
- Time que joga contra defesas fracas
- Goleadas que inflam estatísticas
- Dados de temporadas diferentes

### 2. Contexto Ignorado
- Importância do jogo
- Motivação dos times
- Condições climáticas

### 3. Overconfidence
- Confiar 100% em estatísticas
- Ignorar fatores humanos
- Esquecer da aleatoriedade

## Como Usar Nossa Análise

1. **Leia o Reasoning**: Entenda PORQUE recomendamos
2. **Verifique Confidence**: Maior confidence = maior certeza
3. **Considere EV**: Quanto maior, melhor a oportunidade
4. **Respeite Stake**: Nossa sugestão considera risco

## Próxima Lição
Aprenda sobre **Confidence Score** e como usá-lo nas suas decisões.
                """,
                level=LessonLevel.BEGINNER,
                type=LessonType.TEXT,
                duration_minutes=20,
                prerequisites=["fundamentals_001"],
                learning_objectives=[
                    "Entender como coletamos e processamos dados",
                    "Reconhecer ajustes de contexto",
                    "Evitar armadilhas comuns de interpretação"
                ],
                practical_examples=[
                    {
                        "scenario": "Barcelona vs Real Sociedad",
                        "analysis": "Barça 2.3 gols/jogo, mas Sociedad sofre apenas 1.1/jogo",
                        "adjustment": "Gols esperados: 2.3 × (1.1/1.4) = 1.8 gols",
                        "insight": "Defesa da Sociedad reduz ataque do Barcelona"
                    }
                ],
                quiz_questions=[
                    {
                        "question": "Por que ajustamos estatísticas pela qualidade do adversário?",
                        "options": [
                            "Para complicar",
                            "Para ter contexto real",
                            "É opcional",
                            "Não ajustamos"
                        ],
                        "correct": 1,
                        "explanation": "Contexto é fundamental - um time pode ter boas stats contra adversários fracos"
                    }
                ],
                completion_reward=150
            ),

            # MÓDULO 2: CONCEITOS INTERMEDIÁRIOS
            Lesson(
                id="intermediate_001",
                title="🎯 Confidence Score: Quando Confiar",
                description="Aprenda a interpretar nosso sistema de confiança",
                content="""
# 🎯 Confidence Score - Medindo Nossa Certeza

## O que é Confidence Score?

O **Confidence Score** (0-10) indica o quão **confiantes** estamos em nossa análise. Não é a probabilidade de acerto, mas sim a **qualidade da informação** disponível.

## Escala de Confidence

| Score | Interpretação | Ação Recomendada |
|-------|---------------|------------------|
| 9-10 | 🔥 **Altíssima** | Apostar com stake maior |
| 7-8 | ✅ **Alta** | Apostar normalmente |
| 5-6 | ⚠️ **Média** | Apostar com cuidado |
| 3-4 | 🚫 **Baixa** | Evitar |
| 0-2 | ❌ **Péssima** | Nunca apostar |

## Fatores que Influenciam

### ✅ Aumentam Confidence
- **Dados abundantes**: 20+ jogos recentes
- **Padrões consistentes**: Time sempre marca em casa
- **Low variance**: Resultados previsíveis
- **Consenso de modelos**: Todos algoritmos concordam
- **Contexto claro**: Motivação óbvia

### ❌ Diminuem Confidence
- **Poucos dados**: Time novo, liga exótica
- **Alta volatilidade**: Resultados erráticos
- **Fatores externos**: Lesões importantes
- **Modelos divergem**: Algoritmos discordam
- **Incertezas**: Escalação indefinida

## Exemplos Práticos

### 🔥 Confidence 9.2 - Manchester City vs Brighton (Over 2.5)
**Por que confiança alta?**
- City: 2.8 gols/jogo em casa (últimos 15)
- Brighton: 1.9 gols sofridos/jogo fora (consistente)
- H2H: Over 2.5 em 8 dos últimos 10 jogos
- Ambos precisam de pontos (final da temporada)
- **3 modelos ML concordam**: 71% chance Over 2.5

### ⚠️ Confidence 5.1 - Juventus vs Napoli (1X2)
**Por que confiança média?**
- Derby: sempre imprevisível
- Juventus: forma inconsistente (WWLDL)
- Napoli: ótimo fora, mas Juve forte em casa
- Lesões importantes dos dois lados
- **Modelos divididos**: 45% vs 55% vs empate

## Como Usar na Prática

### Estratégia por Confidence

```python
if confidence >= 8.0 and ev >= 10.0:
    stake = 4-5 unidades  # Apostão
elif confidence >= 7.0 and ev >= 8.0:
    stake = 2-3 unidades  # Aposta normal
elif confidence >= 6.0 and ev >= 12.0:
    stake = 1-2 unidades  # EV alto compensa risk
else:
    stake = 0  # Pular
```

### Combinando EV + Confidence

| EV% | Confidence | Decisão |
|-----|------------|---------|
| 15% | 9.0 | 🔥 **MUST BET** |
| 8% | 8.5 | ✅ **BET** |
| 12% | 6.0 | ⚠️ **Cuidado** |
| 6% | 9.0 | 🤔 **Consider** |
| 15% | 4.0 | ❌ **Skip** |

## ⚠️ Armadilhas com Confidence

### 1. Confidence ≠ Probabilidade
- **Errado**: "Confidence 8 = 80% de chance"
- **Correto**: "Confidence 8 = análise muito confiável"

### 2. Low Confidence com High EV
- Às vezes vale a pena (stake menor)
- EV muito alto pode compensar incerteza

### 3. High Confidence com Low EV
- Evitar mesmo com confidence alta
- Sem EV+, não há vantagem matemática

## Dicas Avançadas

### 1. **Paciência**
- Espere picks com confidence 7+
- Qualidade > Quantidade

### 2. **Bankroll Scaling**
- Confidence 9: 5% da banca
- Confidence 7: 3% da banca
- Confidence 6: 1% da banca

### 3. **Tracking**
- Acompanhe performance por faixa de confidence
- Ajuste estratégia baseado em resultados

## Próxima Lição
Aprenda sobre **Gestão de Banca** - como não quebrar nunca.
                """,
                level=LessonLevel.INTERMEDIATE,
                type=LessonType.TEXT,
                duration_minutes=25,
                prerequisites=["fundamentals_001", "fundamentals_002"],
                learning_objectives=[
                    "Entender escala de confidence",
                    "Saber combinar EV + Confidence",
                    "Aplicar na estratégia de stakes"
                ],
                practical_examples=[
                    {
                        "scenario": "Liverpool vs Arsenal - Both Teams Score",
                        "ev": "12.5%",
                        "confidence": "8.3",
                        "reasoning": "Ambos times atacam bem, defesas vulneráveis",
                        "recommendation": "Stake: 3 unidades - Alta confiança + bom EV"
                    }
                ],
                quiz_questions=[
                    {
                        "question": "Pick com EV 15% e Confidence 4.0. O que fazer?",
                        "options": [
                            "Apostar pesado - EV alto",
                            "Evitar - confidence baixo",
                            "Apostar pouco - EV compensa",
                            "Apostar normal"
                        ],
                        "correct": 1,
                        "explanation": "Confidence muito baixo indica análise duvidosa, mesmo com EV alto"
                    }
                ],
                completion_reward=200
            ),

            # MÓDULO 3: GESTÃO DE BANCA
            Lesson(
                id="advanced_001",
                title="💰 Gestão de Banca: A Chave do Sucesso",
                description="Sistema científico para proteger e crescer sua banca",
                content="""
# 💰 Gestão de Banca - Seu Seguro de Vida

## Por que Gestão de Banca?

- 📈 **80% do sucesso** em apostas é gestão de banca
- 🛡️ **Protege contra variance** - sequências de perdas
- 📊 **Maximiza crescimento** a longo prazo
- 🧠 **Remove emoção** das decisões

## Métodos de Gestão

### 1. 🔥 **Kelly Criterion** (Nossa Recomendação)
```
Stake % = (EV × Confidence) / 100
```

**Exemplo:**
- EV: 12%
- Confidence: 8.0
- Kelly = (12 × 8) / 100 = 0.96%
- **Stake**: 1% da banca

### 2. ✅ **Flat Betting** (Conservador)
- Sempre **1-3% da banca**
- Simples e seguro
- Crescimento mais lento

### 3. ⚠️ **Fixed Units** (Intermediário)
- Define unidades (1 unidade = 1% da banca)
- Stakes: 1-5 unidades baseado em EV/Confidence
- Reajusta unidades mensalmente

## Sistema QuantumBet

### Stake Suggestions (0-10)
```python
def calculate_stake(ev, confidence):
    if ev < 5:
        return 0  # Não apostar
    
    kelly_fraction = (ev * confidence) / 100
    
    # Conservative Kelly (50% do Kelly full)
    stake_pct = kelly_fraction * 0.5
    
    # Convert to 0-10 scale
    return min(stake_pct * 200, 10)
```

### Interpretação
- **0-1**: Pular ou stake mínimo
- **2-3**: Stake normal  
- **4-5**: Stake elevado
- **6-7**: Stake alto
- **8-10**: Stake máximo (raramente)

## Regras de Ouro

### 1. 🚫 **Nunca mais de 5% por pick**
- Mesmo com EV 20% e Confidence 10
- Proteção contra black swans

### 2. 📊 **Máximo 15% da banca por dia**
- Limite exposição diária
- Evita overexposure

### 3. 🔄 **Reajuste mensal**
- Recalcule valor da unidade
- Banca cresceu? Aumente stakes
- Banca diminuiu? Reduza stakes

### 4. 💿 **Stop Loss Mental**
- Se perder 20% da banca inicial
- Pare e reavalie estratégia
- Volte com stakes menores

## Simulação Prática

### Cenário: Banca R$ 1.000

| Pick | EV | Conf | Stake Sugerido | Valor | Resultado | Nova Banca |
|------|----|----- |----------------|-------|-----------|-------------|
| 1 | 12% | 8.0 | 2.4 units (2.4%) | R$ 24 | +R$ 18 | R$ 1.018 |
| 2 | 8% | 7.5 | 1.5 units (1.5%) | R$ 15 | -R$ 15 | R$ 1.003 |
| 3 | 15% | 9.0 | 3.4 units (3.4%) | R$ 34 | +R$ 51 | R$ 1.054 |

**Após 3 picks**: +5.4% de crescimento

## Erros Comuns

### ❌ **Chase Losses**
- Aumentar stakes após perdas
- Receita para falência
- **Solução**: Discipline rígida

### ❌ **Get Rich Quick**
- Stakes muito altos
- "Essa é certeza!"
- **Solução**: Foque no longo prazo

### ❌ **Ignore Variance**  
- "Perdi 5 seguidas, sistema não funciona"
- Variance é normal
- **Solução**: Mínimo 100 picks para avaliar

### ❌ **Emotional Betting**
- Apostar por paixão no time
- Dobrar stakes em clássicos
- **Solução**: Robotic discipline

## Planos de Crescimento

### 🥉 **Conservador** (Goal: +20% ano)
- Stakes: 0.5-2% da banca
- Apenas picks com EV 10%+ e Conf 7+
- ~50 picks/ano

### 🥈 **Moderado** (Goal: +40% ano)  
- Stakes: 1-3% da banca
- Picks com EV 8%+ e Conf 6+
- ~100 picks/ano

### 🥇 **Agressivo** (Goal: +80% ano)
- Stakes: 1-5% da banca
- Picks com EV 6%+ e Conf 5+
- ~200 picks/ano
- **⚠️ Maior risco**

## Ferramentas

### Calculadora de Stakes
```
Banca Atual: R$ 1.000
EV do Pick: 12%
Confidence: 8.5
Kelly Conservativo: 2.04%
Stake Recomendado: R$ 20.40
```

### Tracking Sheet
- Data, Pick, EV, Confidence, Stake, Resultado
- ROI acumulado
- Drawdown máximo
- Sharpe ratio

## Próxima Lição
**Psychology of Betting** - Como manter disciplina mental.
                """,
                level=LessonLevel.ADVANCED,
                type=LessonType.TEXT,
                duration_minutes=35,
                prerequisites=["intermediate_001"],
                learning_objectives=[
                    "Dominar Kelly Criterion",
                    "Implementar sistema de stakes",
                    "Evitar erros fatais de gestão"
                ],
                practical_examples=[
                    {
                        "scenario": "Banca R$ 2.000, Pick EV 10%, Confidence 7.5",
                        "kelly_calc": "(10 × 7.5) / 100 = 0.75%",
                        "conservative": "0.75% × 0.5 = 0.375%",
                        "stake": "R$ 7.50 (muito conservador, pode apostar R$ 15)"
                    }
                ],
                quiz_questions=[
                    {
                        "question": "Com banca R$ 1.000, qual stake máximo por pick?",
                        "options": ["R$ 100", "R$ 50", "R$ 30", "R$ 20"],
                        "correct": 1,
                        "explanation": "Máximo 5% da banca = R$ 50"
                    }
                ],
                completion_reward=300
            )
        ]
    
    async def get_lesson(self, lesson_id: str) -> Optional[Lesson]:
        """Retorna lição específica"""
        for lesson in self.lessons:
            if lesson.id == lesson_id:
                return lesson
        return None
    
    async def get_lessons_by_level(self, level: LessonLevel) -> List[Lesson]:
        """Retorna lições de um nível específico"""
        return [lesson for lesson in self.lessons if lesson.level == level]
    
    async def get_user_progress(self, user_id: str) -> UserProgress:
        """Retorna progresso do usuário"""
        # Simulação - em produção buscaria do banco
        return UserProgress(
            user_id=user_id,
            completed_lessons=["fundamentals_001", "fundamentals_002"],
            current_level=LessonLevel.INTERMEDIATE,
            total_xp=250,
            certificates_earned=[],
            last_activity=datetime.now()
        )
    
    async def complete_lesson(self, user_id: str, lesson_id: str, quiz_score: Optional[float] = None) -> Dict:
        """Marca lição como completa"""
        
        lesson = await self.get_lesson(lesson_id)
        if not lesson:
            return {"error": "Lição não encontrada"}
        
        # Verificar pré-requisitos
        user_progress = await self.get_user_progress(user_id)
        missing_prereqs = [p for p in lesson.prerequisites if p not in user_progress.completed_lessons]
        
        if missing_prereqs:
            return {
                "error": "Pré-requisitos não cumpridos",
                "missing": missing_prereqs
            }
        
        # Verificar quiz se necessário
        if lesson.quiz_questions and quiz_score is not None:
            if quiz_score < 0.7:  # 70% mínimo
                return {
                    "error": "Score insuficiente no quiz",
                    "required": 70,
                    "achieved": quiz_score * 100
                }
        
        # Simular salvamento no banco
        # Em produção: salvar completion, atualizar XP, etc.
        
        return {
            "success": True,
            "lesson_completed": lesson_id,
            "xp_earned": lesson.completion_reward,
            "total_xp": user_progress.total_xp + lesson.completion_reward,
            "next_recommendations": await self._get_next_recommendations(user_id, lesson_id)
        }
    
    async def get_learning_path(self, user_id: str) -> Dict:
        """Retorna caminho de aprendizado personalizado"""
        
        user_progress = await self.get_user_progress(user_id)
        
        # Próximas lições recomendadas
        available_lessons = []
        for lesson in self.lessons:
            if lesson.id not in user_progress.completed_lessons:
                # Verificar se pode fazer (pré-requisitos)
                can_do = all(p in user_progress.completed_lessons for p in lesson.prerequisites)
                if can_do:
                    available_lessons.append(lesson)
        
        # Ordenar por nível e dependências
        available_lessons.sort(key=lambda x: (x.level.value, len(x.prerequisites)))
        
        return {
            "user_level": user_progress.current_level.value,
            "progress_percentage": len(user_progress.completed_lessons) / len(self.lessons) * 100,
            "completed_lessons": len(user_progress.completed_lessons),
            "total_lessons": len(self.lessons),
            "total_xp": user_progress.total_xp,
            "next_recommended": available_lessons[:3],  # Top 3 próximas
            "current_focus": self._determine_focus_area(user_progress),
            "estimated_completion": self._estimate_completion_time(user_progress)
        }
    
    async def generate_personalized_content(self, user_id: str, topic: str) -> Dict:
        """Gera conteúdo personalizado baseado no nível do usuário"""
        
        user_progress = await self.get_user_progress(user_id)
        
        # Ajustar explicação baseado no nível
        if user_progress.current_level == LessonLevel.BEGINNER:
            explanation_style = "simples e prático"
            examples = "básicos com números simples"
        elif user_progress.current_level == LessonLevel.INTERMEDIATE:
            explanation_style = "detalhado com contexto"
            examples = "cenários reais"
        else:
            explanation_style = "técnico e avançado"
            examples = "casos complexos"
        
        return {
            "topic": topic,
            "user_level": user_progress.current_level.value,
            "explanation_style": explanation_style,
            "content": f"Conteúdo personalizado sobre {topic} para nível {user_progress.current_level.value}",
            "practical_exercises": await self._generate_exercises(topic, user_progress.current_level),
            "additional_resources": await self._get_additional_resources(topic)
        }
    
    async def _get_next_recommendations(self, user_id: str, completed_lesson_id: str) -> List[str]:
        """Recomenda próximas lições"""
        
        # Buscar lições que têm a completada como pré-requisito
        next_lessons = []
        for lesson in self.lessons:
            if completed_lesson_id in lesson.prerequisites:
                next_lessons.append(lesson.id)
        
        return next_lessons[:2]  # Máximo 2 recomendações
    
    def _determine_focus_area(self, user_progress: UserProgress) -> str:
        """Determina área de foco baseada no progresso"""
        
        completed = user_progress.completed_lessons
        
        if not completed:
            return "Fundamentos - Comece aqui!"
        elif len(completed) < 3:
            return "Conceitos Básicos"
        elif len(completed) < 6:
            return "Aplicação Prática"
        else:
            return "Estratégias Avançadas"
    
    def _estimate_completion_time(self, user_progress: UserProgress) -> str:
        """Estima tempo para completar curso"""
        
        remaining_lessons = len(self.lessons) - len(user_progress.completed_lessons)
        avg_time_per_lesson = 20  # minutos
        
        total_minutes = remaining_lessons * avg_time_per_lesson
        hours = total_minutes // 60
        
        if hours < 2:
            return f"{total_minutes} minutos"
        elif hours < 10:
            return f"{hours} horas"
        else:
            return f"{hours//7} semanas (1h por dia)"
    
    async def _generate_exercises(self, topic: str, level: LessonLevel) -> List[Dict]:
        """Gera exercícios práticos"""
        
        if topic == "expected_value":
            return [
                {
                    "exercise": "Calcule o EV",
                    "scenario": "Odds 2.50, Probabilidade real 45%",
                    "solution": "EV = (0.45 × 2.50) - 1 = +12.5%"
                }
            ]
        
        return []
    
    async def _get_additional_resources(self, topic: str) -> List[Dict]:
        """Recursos adicionais"""
        
        return [
            {
                "type": "article",
                "title": "Expected Value em Profundidade",
                "url": "/resources/ev-guide",
                "duration": "10 min"
            },
            {
                "type": "calculator",
                "title": "Calculadora de EV",
                "url": "/tools/ev-calculator", 
                "description": "Ferramenta prática"
            }
        ] 