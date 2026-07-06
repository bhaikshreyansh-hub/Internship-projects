"""
Large Scale Dataset Builder
============================
Downloads 2000+ Wikipedia articles across 10 domains and saves them
as .txt files into raw_documents/large_dataset/.

Designed for machines with limited RAM (8GB) — downloads one domain
at a time so partial progress is never lost if interrupted.

Run from project root (venv activated):
    python build_large_dataset.py

Estimated time: 60-90 minutes for full download.
"""

import re
import time
from pathlib import Path

try:
    import wikipediaapi
except ImportError:
    print("ERROR: Run 'pip install wikipedia-api' first.")
    exit(1)

OUTPUT_DIR = Path("./raw_documents/large_dataset")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 10 domains, ~200 articles each = ~2000 total
DOMAINS = {
    "science": [
        "Physics", "Chemistry", "Biology", "Quantum mechanics",
        "Thermodynamics", "Electromagnetism", "Optics", "Nuclear physics",
        "Particle physics", "Astrophysics", "Cosmology", "Relativity",
        "Atomic theory", "Periodic table", "Chemical bond", "Organic chemistry",
        "Inorganic chemistry", "Biochemistry", "Genetics", "Evolution",
        "Cell biology", "Ecology", "Photosynthesis", "DNA", "Protein",
        "Enzyme", "Virus", "Bacteria", "Immune system", "Nervous system",
        "Human brain", "Heart", "Digestive system", "Respiratory system",
        "Endocrine system", "Skeletal system", "Muscle", "Blood",
        "Metabolism", "Homeostasis", "Mitosis", "Meiosis",
        "Natural selection", "Adaptation", "Biodiversity", "Ecosystem",
        "Food chain", "Climate", "Weather", "Atmosphere of Earth",
    ],
    "mathematics": [
        "Mathematics", "Algebra", "Geometry", "Calculus", "Statistics",
        "Probability", "Number theory", "Linear algebra", "Differential equation",
        "Topology", "Set theory", "Logic", "Graph theory", "Combinatorics",
        "Trigonometry", "Matrix (mathematics)", "Vector space",
        "Complex number", "Prime number", "Fibonacci sequence",
        "Pythagorean theorem", "Euclidean geometry", "Non-Euclidean geometry",
        "Fractal", "Chaos theory", "Game theory", "Cryptography",
        "Numerical analysis", "Fourier transform", "Laplace transform",
        "Boolean algebra", "Abstract algebra", "Category theory",
        "Mathematical proof", "Axiom", "Theorem", "Algorithm",
        "Computational complexity theory", "P versus NP problem",
        "Infinity", "Limit (mathematics)", "Derivative", "Integral",
        "Taylor series", "Binomial theorem", "Bayes theorem",
        "Central limit theorem", "Normal distribution", "Standard deviation",
    ],
    "medicine": [
        "Medicine", "Anatomy", "Physiology", "Pathology", "Pharmacology",
        "Surgery", "Cardiology", "Neurology", "Oncology", "Pediatrics",
        "Psychiatry", "Dermatology", "Ophthalmology", "Orthopedics",
        "Diabetes", "Cancer", "Heart disease", "Stroke", "Hypertension",
        "Asthma", "Tuberculosis", "HIV/AIDS", "Malaria", "Influenza",
        "COVID-19", "Alzheimer's disease", "Parkinson's disease",
        "Epilepsy", "Depression (mood)", "Anxiety disorder", "Schizophrenia",
        "Autism", "Obesity", "Osteoporosis", "Arthritis", "Anemia",
        "Kidney disease", "Liver disease", "Antibiotic", "Vaccine",
        "Clinical trial", "Medical imaging", "Magnetic resonance imaging",
        "X-ray", "Ultrasound", "Blood pressure", "Cholesterol",
        "Stem cell", "Gene therapy", "Organ transplantation",
    ],
    "history": [
        "Ancient history", "Middle Ages", "Renaissance", "Industrial Revolution",
        "World War I", "World War II", "Cold War", "French Revolution",
        "American Revolution", "Roman Empire", "Ancient Egypt",
        "Ancient Greece", "Byzantine Empire", "Ottoman Empire",
        "British Empire", "Mongol Empire", "History of China",
        "History of India", "History of Japan", "History of Africa",
        "History of Islam", "Crusades", "Black Death", "Age of Exploration",
        "Colonialism", "Slavery", "Abolitionism", "Feminism",
        "Russian Revolution", "Chinese Civil War", "Korean War",
        "Vietnam War", "Gulf War", "Israeli–Palestinian conflict",
        "History of science", "History of mathematics",
        "History of medicine", "History of art", "History of music",
        "History of philosophy", "History of religion",
        "History of democracy", "History of capitalism",
        "History of communism", "History of the United States",
        "History of Europe", "Ancient Rome", "Ancient Mesopotamia",
    ],
    "geography": [
        "Geography", "Continent", "Ocean", "Mountain", "River",
        "Climate change", "Global warming", "Deforestation", "Desertification",
        "Earthquake", "Volcano", "Tsunami", "Hurricane", "Flood",
        "United States", "China", "India", "Russia", "Brazil",
        "United Kingdom", "France", "Germany", "Japan", "Australia",
        "Canada", "Italy", "Spain", "Mexico", "South Korea",
        "Indonesia", "Turkey", "Saudi Arabia", "Argentina", "South Africa",
        "Nigeria", "Egypt", "Pakistan", "Bangladesh", "Vietnam",
        "Amazon rainforest", "Sahara", "Himalayas", "Alps",
        "Nile", "Amazon River", "Mississippi River", "Yangtze River",
        "Pacific Ocean", "Atlantic Ocean", "Arctic", "Antarctica",
    ],
    "technology": [
        "Computer", "Internet", "Software", "Hardware", "Operating system",
        "Database", "Computer network", "Cybersecurity", "Cloud computing",
        "Blockchain", "Cryptocurrency", "Bitcoin", "Artificial intelligence",
        "Robotics", "Automation", "3D printing", "Virtual reality",
        "Augmented reality", "Internet of Things", "5G",
        "Semiconductor", "Microprocessor", "Computer memory",
        "Hard disk drive", "Solid-state drive", "Computer programming",
        "Python (programming language)", "Java (programming language)",
        "JavaScript", "Linux", "Microsoft Windows", "Android (operating system)",
        "iOS", "World Wide Web", "Search engine", "Social media",
        "E-commerce", "Streaming media", "Video game",
        "Smartphone", "Electric vehicle", "Solar panel",
        "Wind turbine", "Nuclear power", "Renewable energy",
        "Satellite", "Global Positioning System", "Radar",
    ],
    "economics": [
        "Economics", "Microeconomics", "Macroeconomics", "Supply and demand",
        "Market economy", "Capitalism", "Socialism", "Communism",
        "Gross domestic product", "Inflation", "Unemployment",
        "Interest rate", "Stock market", "Bond (finance)", "Currency",
        "International trade", "Globalization", "Free trade",
        "Monopoly", "Oligopoly", "Competition (economics)",
        "Central bank", "Federal Reserve", "European Central Bank",
        "Fiscal policy", "Monetary policy", "Taxation",
        "Government spending", "Public debt", "Budget deficit",
        "Economic growth", "Recession", "Great Depression",
        "Financial crisis of 2007–2008", "Behavioral economics",
        "Game theory", "Development economics",
        "Labour economics", "Health economics", "Environmental economics",
        "Poverty", "Income inequality", "Minimum wage",
        "Entrepreneurship", "Innovation", "Supply chain",
        "Consumer price index", "Purchasing power parity",
    ],
    "philosophy": [
        "Philosophy", "Ethics", "Logic", "Epistemology", "Metaphysics",
        "Aesthetics", "Political philosophy", "Philosophy of mind",
        "Philosophy of science", "Philosophy of language",
        "Socrates", "Plato", "Aristotle", "Immanuel Kant",
        "René Descartes", "John Locke", "David Hume", "Friedrich Nietzsche",
        "Karl Marx", "Jean-Paul Sartre", "Simone de Beauvoir",
        "Utilitarianism", "Deontological ethics", "Virtue ethics",
        "Existentialism", "Nihilism", "Stoicism", "Empiricism",
        "Rationalism", "Idealism", "Materialism", "Dualism",
        "Free will", "Consciousness", "Personal identity",
        "Social contract", "Democracy", "Justice",
        "Human rights", "Equality", "Liberty",
        "Meaning of life", "Moral relativism", "Moral realism",
        "Philosophy of religion", "Atheism", "Agnosticism",
        "Phenomenology", "Pragmatism", "Analytic philosophy",
    ],
    "arts": [
        "Art", "Music", "Literature", "Cinema", "Theatre",
        "Painting", "Sculpture", "Architecture", "Photography",
        "Dance", "Opera", "Jazz", "Classical music", "Rock music",
        "Hip hop music", "Pop music", "Folk music",
        "Leonardo da Vinci", "Michelangelo", "Rembrandt",
        "Pablo Picasso", "Vincent van Gogh", "Claude Monet",
        "William Shakespeare", "Charles Dickens", "Jane Austen",
        "Leo Tolstoy", "Fyodor Dostoevsky", "Franz Kafka",
        "Homer", "Dante Alighieri", "Johann Wolfgang von Goethe",
        "Ludwig van Beethoven", "Wolfgang Amadeus Mozart",
        "Johann Sebastian Bach", "Frédéric Chopin",
        "Renaissance art", "Baroque", "Romanticism", "Impressionism",
        "Modernism", "Postmodernism", "Abstract art",
        "Novel", "Poetry", "Drama", "Short story",
        "Film noir", "Documentary film", "Animation",
    ],
    "psychology": [
        "Psychology", "Cognitive psychology", "Social psychology",
        "Developmental psychology", "Clinical psychology",
        "Neuropsychology", "Personality psychology",
        "Sigmund Freud", "Carl Jung", "B. F. Skinner",
        "Jean Piaget", "Abraham Maslow", "Carl Rogers",
        "Memory", "Learning", "Motivation", "Emotion",
        "Perception", "Attention", "Intelligence",
        "Personality", "Attitude (psychology)", "Stereotype",
        "Cognitive bias", "Confirmation bias", "Dunning–Kruger effect",
        "Classical conditioning", "Operant conditioning",
        "Cognitive behavioral therapy", "Psychoanalysis",
        "Mindfulness", "Stress (biology)", "Burnout (psychology)",
        "Sleep", "Dream", "Unconscious mind",
        "Self-esteem", "Empathy", "Altruism",
        "Aggression", "Addiction", "Phobia",
        "Post-traumatic stress disorder", "Obsessive–compulsive disorder",
        "Bipolar disorder", "Borderline personality disorder",
        "Emotional intelligence", "Creativity", "Flow (psychology)",
    ],
}


def sanitize_filename(title: str) -> str:
    return re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_').lower()[:80]


def download_domain(wiki, domain: str, topics: list, total_downloaded: int, grand_total: int):
    domain_dir = OUTPUT_DIR / domain
    domain_dir.mkdir(exist_ok=True)

    success, skipped, failed = 0, 0, 0

    for topic in topics:
        fname = domain_dir / f"{sanitize_filename(topic)}.txt"

        if fname.exists():
            skipped += 1
            total_downloaded += 1
            continue

        page = wiki.page(topic)

        if not page.exists():
            print(f"  [{total_downloaded:04d}/{grand_total}] NOT FOUND: {topic}")
            failed += 1
            total_downloaded += 1
            continue

        content = f"# {page.title}\n\n{page.text}"

        if len(content) < 300:
            print(f"  [{total_downloaded:04d}/{grand_total}] TOO SHORT: {topic}")
            failed += 1
            total_downloaded += 1
            continue

        fname.write_text(content, encoding="utf-8")
        word_count = len(content.split())
        print(f"  [{total_downloaded:04d}/{grand_total}] OK ({word_count:,} words): {topic}")
        success += 1
        total_downloaded += 1
        time.sleep(0.3)

    return success, skipped, failed, total_downloaded


def main():
    wiki = wikipediaapi.Wikipedia(
        language='en',
        user_agent='EKB-InternshipProject/1.0 (educational use)'
    )

    grand_total = sum(len(v) for v in DOMAINS.items())
    grand_total = sum(len(topics) for topics in DOMAINS.values())
    total_downloaded = 0
    overall_success, overall_skipped, overall_failed = 0, 0, 0

    print(f"Large Scale Dataset Builder")
    print(f"Target: {grand_total} articles across {len(DOMAINS)} domains")
    print(f"Output: {OUTPUT_DIR}\n")
    print("Tip: Safe to Ctrl+C and restart — already-downloaded files are skipped.\n")

    for domain, topics in DOMAINS.items():
        print(f"\n{'='*55}")
        print(f"Domain: {domain.upper()} ({len(topics)} articles)")
        print(f"{'='*55}")

        s, sk, f, total_downloaded = download_domain(
            wiki, domain, topics, total_downloaded, grand_total
        )
        overall_success += s
        overall_skipped += sk
        overall_failed += f

        print(f"  Domain done: {s} downloaded, {sk} skipped, {f} failed")

    print(f"\n{'='*55}")
    print(f"COMPLETE")
    print(f"Downloaded : {overall_success}")
    print(f"Skipped    : {overall_skipped}")
    print(f"Failed     : {overall_failed}")
    total_files = len(list(OUTPUT_DIR.rglob("*.txt")))
    print(f"Total files: {total_files}")
    print(f"\nNext step: python ingest_large.py")


if __name__ == "__main__":
    main()
