import logging
from src.pipeline import Pipeline
from src.providers.critic_agg import CriticAggProvider
from src.providers.audience_pulse import AudiencePulseProvider
from src.providers.box_office_metrics import BoxOfficeMetricsProvider

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


def main():
    providers = [
        CriticAggProvider("data/provider1.csv"),
        AudiencePulseProvider("data/provider2.json"),
        BoxOfficeMetricsProvider(
            "data/provider3_domestic.csv",
            "data/provider3_international.csv",
            "data/provider3_financials.csv",
        ),
    ]

    dataset = Pipeline(providers).run()

    print(f"\n{'='*60}")
    print(f"  Movie Score Pipeline — {len(dataset.all())} films loaded")
    print(f"{'='*60}\n")

    for movie in dataset.all():
        print(f"  {movie.title} ({movie.year})")
        print(f"    Critic score:      {movie.critic_score_pct}%  (top: {movie.top_critic_score})")
        print(f"    Audience score:    {movie.audience_avg_score}")
        print(f"    Worldwide BO:      ${movie.worldwide_box_office:,}" if movie.worldwide_box_office else "    Worldwide BO:      N/A")
        print(f"    Production budget: ${movie.production_budget:,}" if movie.production_budget else "    Production budget: N/A")
        print()


if __name__ == "__main__":
    main()
