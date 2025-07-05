# VLM-based Assessment of SCOOTER Images

In this folder, you can find all the generated ratings per attack + code to process the data at hand. We used OpenAI's GPT-4o model to automatically annotate data.

## Summarizing Existing Data
We provide the generated ratings in `*.json` files. E.g., the ratings for real images are stored within `real.json`. You can summarize the VLM-statistics per attack by running the following:

```bash
python ratings_summary.py --attack_name <attack_name>
```

which accepts the following keys:
 - Real Images: `real`
 - SemanticAdv: `semanticadv`
 - NCF: `ncf`
 - cAdv: `cadv`
 - DiffAttack (DA): `diffattack`
 - AdvPP: `advpp`
 - ACA: `aca`


## Perform 4o-based Assessments

This folder also contains `gpt_4o_assessment.py` which allows you to a VLM-based evaluation of your images by specifying an image directory through `--img_dir`. For example, you can assess our provided sample images by simpling running the following:

```bash
python gpt_4o_assessment.py --img_dir sample_images
```

> [!NOTE]
> You need to create an `.env` file in this directory and add your OpenAI API key as a line akin to `OPENAI_API_KEY=your-api-key-here`.

