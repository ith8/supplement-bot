![logo](src/logo.png "SuppleMentor")

# SuppleMentor
Transform your supplement management with SuppleMentor. Get customized expert advice on dosages, avoid interactions, and tailor your regimen for sharper focus, better sleep, and optimal fitness.

Overwhelmed by the vast landscape of over 100 supplements, each with its potential interactions, effective dosages, and side effects? Uncertain if a particular supplement is right for your specific needs? Enter SuppleMentor, manage your supplement routine at scale.

- **Personalized Health Insights**: SuppleMentor crafts a detailed health profile for each user, integrating data from their weight, age, sex, health tests, medication, and allergy records.

- **AI-Driven Recommendations**: Leveraging AI, SuppleMentor delivers a customized supplement plan focused on enhancing mental focus, sleep quality, and workout performance. It provides tailored starting dosages based on demographic and personal health needs, and it meticulously highlights potential side effects and drug interactions relevant to the user's specific health profile.

- **Interactive Management Tool**: Users can effortlessly track and manage their current supplement intake through our intuitive interface. By aggregating user feedback on side effects and satisfaction, SuppleMentor continuously refines and improves its recommendations.

## Installation
Ensure you have Python 3.10 installed on your system. Then clone this repository:

```bash
git clone [repository-link]
cd [repository-directory]
```

Install the required packages:

```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create your own .env file with the following variables:

```bash
OPENAI_API_KEY=[your-openai-api-key]
```

## Usage
To run the Streamlit app:

```bash
streamlit run src/Home.py
```