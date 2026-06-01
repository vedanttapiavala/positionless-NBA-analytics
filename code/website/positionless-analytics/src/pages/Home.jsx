import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, BarChart, Bar, Cell
} from 'recharts'
import PositionPredictability from '../components/PositionPredictability'
import CatBoostSHAP from '../components/CatBoostSHAP'
import SHAPpositionlessScatter from '../components/SHAPpositionlessScatter'
import InteractionForestPlot from '../components/InteractionForestPlot'
// In accordance with this course's AI policy, Claude and ChatGPT were used for much of the code 
// in this document, especially code related to UI/UX. However, all words and figures are my own.
const ORANGE  = '#f7630c'
const ORANGE2 = '#ff8c42'
const TEXT2   = '#9090aa'

function StatCard({ label, value, sub}) {
  return (
    <div
        style={{
            border: "1px solid #2a2a3e",
            borderRadius: "12px",
            padding: "16px",
            background: "#12121a",
            boxShadow: "0 1px 3px rgba(0,0,0,0.4)",
            transition: "transform 200ms ease, box-shadow 200ms ease",
            color: "#cccccc"
        }}
        onMouseEnter={(e) => {
            e.currentTarget.style.transform = "translateY(-4px)";
            e.currentTarget.style.boxShadow =
            "0 10px 20px rgba(0,0,0,0.6)";
        }}
        onMouseLeave={(e) => {
            e.currentTarget.style.transform = "translateY(0px)";
            e.currentTarget.style.boxShadow =
            "0 1px 3px rgba(0,0,0,0.4)";
        }}
        >
        <h3 style={{ fontSize: "18px", fontWeight: 600, marginBottom: "8px", color: "#cccccc" }}>
            {value}
        </h3>

        <p style={{ fontSize: "14px", color: "#aaaaaa", lineHeight: 1.4 }}>
           {sub}
        </p>
    </div>
  )
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background: '#12121a', border: '1px solid #2a2a3e', borderRadius: 6, padding: '8px 12px', fontSize: 12, fontFamily: 'JetBrains Mono, monospace' }}>
      <div style={{ color: '#9090aa', marginBottom: 4 }}>{label}</div>
      {payload.map(p => (
        <div key={p.name} style={{ color: p.color || ORANGE }}>
          {p.name}: <strong>{typeof p.value === 'number' ? p.value.toFixed(3) : p.value}</strong>
        </div>
      ))}
    </div>
  )
}

export default function Home({ data }) {
  const agg  = data?.dashboardAggregates  || {}
  const players = data?.playersIndexTable || []
  const tops = [...players]
  .sort((a, b) => b.positionless_index - a.positionless_index)
  .slice(0, 10)
  .map(row => ({
      label: `${row.Name} (${row.season})`,
      player: row.Name,
      season: row.season,
      positionless_index: row.positionless_index
  }))
  const scat = []

  return (
    <div className="page">
      <div className="page-title">
        Positionless Basketball<br />
        <span className="accent">& Injury Risk</span>
      </div>
      <div className="page-subtitle">
        A machine learning analysis of positionless basketball in the NBA and its relation, if any, to 
        increased injuries.
      </div>

      {/* Stat cards */}
      <div className="stat-grid">
        <StatCard
          label="Player–Game Observations"
          value={agg.player_games ? `${agg.player_games.toLocaleString()}` : '—'}
          sub="Player-Game observations across all seasons analyzed"
        />
        <StatCard
          label="Unique Players"
          value={agg.players ? agg.players.toLocaleString() : '—'}
          sub="players in the study cohort"
        />
        <StatCard
          label="Structural Shift Year"
          value={agg.structural_shift_year || '2019'}
          sub="Breakpoint in positional fluidity"
        />
        <StatCard
          label="Injury Odds Ratio"
          value='+8.1%'
          sub="Injury odds per standard deviation increase in positionless increase"
        />
      </div>

      <hr className="divider" />

      {/* Research question */}
      <div className="section">
        <div className="section-label">Research Question</div>
        <div className="section-title">When did the NBA go positionless?<br></br>Does this relate to the increased 
          amount of injuries?
        </div>
        <p>
          Analysts, players, and NBA Commissioner Adam Silver have mentioned the increased positionless nature
          of the game. When did this happen? Guards rebound, and we see 7'5" centers shooting threes from
          halfcourt. <br></br>
          This study asks: <strong style={{color:'var(--text)'}}>
            <ol>How do we quantify positionless basketball?</ol>
            <ol>When did it accelerate?</ol>
            <ol>Are more positionless players at increased injury risk?</ol></strong>
        </p>
        <p>
          We introduce a continuous <strong style={{color:'var(--text)'}}>Positionless Index</strong>, a quantifiable
          measure of positionless basketball played on a per player-season basis.
          We use this index to model injury probability via Logistic Regressions and CatBoost classifiers
          while adjusting for workload, playstyle, and team context.
        </p>
      </div>

      {/* Data */}
      <div className="section">
        <div className="section-label">Data</div>
        <div className="section-title">Sources & Coverage</div>
        <p>
          This study combines several datasets, including:
          <ul><li>
            <a href='https://www.kaggle.com/datasets/eoinamoore/historical-nba-data-and-player-box-scores' target='_blank'>
          <strong>NBA Box Scores - Player and Team Statistics</strong></a>
          <blockquote class='indented'>NBA regular season, playoff, and play-in games were analyzed from 1983-84 through 2025–26. 
          Individual player games were analyzed for all players logging at least 10 minutes and one field goal attempt.
          Overall, this led to the inclusion of over 870,000 player–game records.
          Each record includes box-score statistics for both the player and the team.</blockquote>
          </li>
          <li>
            <a href='https://www.basketball-reference.com/leagues/NBA_2026_totals.html' target='_blank'>
              <strong>
                Basketball Reference Season Totals
              </strong>
            </a>
              <blockquote class='indented'>
                  Basketball Reference season-level tables were scraped to find players' positions.
              </blockquote>
          </li>
          <li>
            <a href='https://hashtagbasketball.com/nba-injury' target='_blank'>
              <strong>
                Injury Reports
              </strong>
            </a>
            <blockquote class='indented'>
              Injury reports from 2011-2025 were included. These were merged with box score, travel, and NBA
              player information to create logistic regression models for mergeable player-game observations.
            </blockquote>
          </li>
          <li>
            <a href='https://github.com/swar/nba_api' target='_blank'>
              <strong>
                NBA Stats API
              </strong>
            </a>
            <blockquote class='indented'>
              Game logs were used to generate travel data for players, and biographical information (e.g.,
              height, weight, and age) were scraped.
            </blockquote>
          </li>
          </ul>
        </p>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '0.75rem' }}>
          {['Box Scores','Basketball Reference','Injury Reports','Travel Data','Biographical Info'].map(t => (
            <span key={t} className="tag">{t}</span>
          ))}
        </div>
      </div>

      {/* Methods */}
      <div className="section">
        <div className="section-label">Methods</div>
        <div className="section-title">Season-Level Player Position Prediction + Positionless Index</div>
        <p>
          After tuning model hyperparameters on aggregated player position data, season-level predictive models
          were constructed. These models were used for two purposes:
          <ol><li><strong>
            Determining accuracy of position prediction within a season. 
            </strong>{" "}
            Increased positionless play was operationally defined as models' inability to 
            accurately predict player positions. Change-point detection using the Pruned Exact Linear Time 
            (PELT) algorithm evaluated when positionless play became more ubiquitous.
          </li>
          <li>
            <strong>
              Generating out-of fold probabilities for each player's position during that season. 
            </strong>{" "}
              Positionless index was calculated as the entropy of the model's probabilities.
          </li>
          </ol>
        </p>
        <div className="section-title">Injury Risk Prediction</div>
        <p>
          Injury risk (if a player got injured in the next 14 days) was modeled using both logistic regression 
          and a CatBoost classifier. Both models included selected covariates related to 3- and 7-game 
          rolling statistics  (e.g., points, assists, blocks, three pointers, field goals, minutes) 
          alongside team context (win percent) and positionless index. The impact of positionless index on 
          injury risk prediction was measured using odds ratios (logistic regression) and SHAP values (CatBoost 
          classifier).
        </p>
      </div>

      {/* Results charts */}
      <div className="section">
        <div className="section-label">Results</div>
        <div className="section-title">Key Findings</div>

        <div className="callout">
          <p>The NBA's evolution towards positionless basketball shifted significantly around the 2018–19 season.
            Players with higher positionless indices face roughly <strong>8.1% higher injury odds</strong> per standard deviation
            increase in the index, controlling for workload, team context, and playstyle.</p>
        </div>
        <div style={{ display: 'flex', gap: '16px', flexDirection: 'column' }}>
        <PositionPredictability />
        <CatBoostSHAP />
        <SHAPpositionlessScatter />
        <InteractionForestPlot />
        </div>
      </div>

      {/* Takeaway */}
      <div className="section">
        <div className="section-label">Takeaway</div>
        <div className="section-title">Recommendations for Teams</div>
        <p>
          The shift to positionless basketball is real and quantifiable. While positional versatility can
          create mismatches and strategic nuances, the players tasked with these skillsets tend to be injured
          more frequently. Specifically, positionless players tasked with spacing seem to be at 
          the highest risk. Given this research, teams may decide to:
          <ol>
            <li> Manage positionless players' skillsets to avoid concentrating
              perimeter creation and spacing responsibilities. </li>
            <li> Train players constrained to one role with additional skillsets, making them more
              positionless.
            </li>
          </ol>
        </p>
      </div>

      <div className="section">
        <div className="section-label">More Resources</div>
        <div className="section-title">Positionless Index Explorer + Injury Risk Dashboard</div>
        <p>
          Use the <a href="/explorer">Positionless Index Explorer</a> to browse the full player-season index table
          and explore how players' games became more or less positionless over time.
          The <a href="/dashboard">Injury Risk Dashboard</a> explores how the ten most important input features
          drive predicted injury probability for a custom player profile.         
        </p>
      </div>
        
      
    </div>
  )
}