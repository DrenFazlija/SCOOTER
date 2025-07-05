# Reproducing the core SCOOTER Metrics

With the provided data and code snippets, you can recalculate the *core* metrics of SCOOTER, which:

- The mean *modified* score of an attack $\mu_{\text{modified}}$, describing the average Likert rating of an adversarial image
- The mean *real* score of an attack $\mu_{\text{real}}$, describing the average Likert rating of an real image (i.e., an ImageNet S-R50-N samle)
- The associated standard deviations $\sigma_{\text{modified}}$ and $\sigma_{\text{real}}$
- The $p$-values for our two hypotheses ($\Delta := \mu_{\text{real}}-\mu_{\text{modified}}$) of our equivalence test:
    - $H_{0,1}: \Delta < \Delta_L = -0.2$
    - $H_{0,2}: \Delta > \Delta_U = +0.2$

## Modified and Real Scores
To calculate the mean scores, std devs., and number of samples of an attack, you can simply run the Python script

```bash
python scooter_metrics.py --attack_name <name_of_attack>
```

which accepts the following keys:
 - SemanticAdv: `semanticadv`
 - NCF: `ncf`
 - cAdv: `cadv`
 - cAdv w/ annotators who only passed 4/6 comprehension checks: `cadv_4_6`
 - DiffAttack (DA): `diffattack`
 - AdvPP: `advpp`
 - ACA: `aca`

## Setup Instructions for `mixed_effect_TOST.R`

To set up and run the `mixed_effect_TOST.R` script, follow these steps:

1. **Install the neccessary R packages through the console**:
    ```r
    install.packages("readr")
    install.packages("lme4")
    install.packages("lmerTest")
    ```

2. **Adjust the filename in Line 21 to the corresponding experiment**:
    - SemanticAdv: `anonymized_semanticadv_with_image_ids.csv`
    - NCF: `anonymized_ncf_with_image_ids.csv`
    - cAdv: `anonymized_cadv_with_image_ids.csv`
    - cAdv (including users who only classified 4/6 comprehension check pairs correctly): `anonymized_cadv_4_6_with_image_ids.csv`
    - DiffAttack (DA): `anonymized_diffattack_with_image_ids.csv`
    - AdvPP: `anonymized_advpp_with_image_ids.csv`
    - ACA: `anonymized_aca_with_image_ids.csv`

3. **Run the code via `Rscript mixed_effect_TOST.R`**