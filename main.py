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

    try:
        dataset = Pipeline(providers).run()
    except (FileNotFoundError, ValueError) as e:
        logging.error("Pipeline aborted: %s", e)
        return
    except Exception as e:
        logging.error("Unexpected error running pipeline: %s", e)
        raise

    print(f"\n{'='*60}")
    print(f"  Movie Score Pipeline — {len(dataset.all())} films loaded")
    print(f"{'='*60}\n")

    for movie in dataset.all():
        print(f"  {movie.title} ({movie.year})")

        if movie.critic_score_pct is not None:
            reviews = f"  reviews: {movie.total_critic_reviews:,}" if movie.total_critic_reviews is not None else ""
            print(f"    Critic score:      {movie.critic_score_pct}%  (top critic: {movie.top_critic_score}{reviews})")
        else:
            print( "    Critic score:      N/A")

        if movie.audience_avg_score is not None:
            ratings = f"  (ratings: {movie.total_audience_ratings:,})" if movie.total_audience_ratings is not None else ""
            print(f"    Audience score:    {movie.audience_avg_score}{ratings}")
        else:
            print( "    Audience score:    N/A")

        domestic = f"${movie.domestic_box_office:,}" if movie.domestic_box_office is not None else "N/A"
        worldwide = f"${movie.worldwide_box_office:,}" if movie.worldwide_box_office is not None else "N/A"
        print(f"    Domestic BO:       {domestic}")
        print(f"    Worldwide BO:      {worldwide}")

        budget = f"${movie.production_budget:,}" if movie.production_budget is not None else "N/A"
        marketing = f"${movie.marketing_spend:,}" if movie.marketing_spend is not None else "N/A"
        print(f"    Budget:            {budget}  |  Marketing: {marketing}")

        print()


if __name__ == "__main__":
    main()
