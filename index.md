# <img src="project_page/favicon.png" width="30" style="vertical-align: text-bottom; margin-right: 6px;" alt="lock icon"/> SCOOTER – A Human Evaluation Framework for Unrestricted Adversarial Examples

[![license badge](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Zenodo](https://img.shields.io/badge/Dataset-10.5281/zenodo.15771501-%231682D4?logo=zenodo)](https://doi.org/10.5281/zenodo.15771501)
[![GitHub](https://img.shields.io/badge/Code-Work%20in%20Progress!-orange?logo=github)](https://github.com/DrenFazlija/Scooter)



<p align="center">
  <img src="project_page/l3s-logo-c.webp" align="middle" width="200" style="margin-right:40px;"/>
  <img src="project_page/eon.png" align="middle" width="200" style="margin-right:40px;">
  <img src="project_page/UNI-Logo-en-rgb.png" align="middle" width="200" style="margin-right:40px;">
  <img src="project_page/zlga.jpg" align="middle" width="200">
</p>

<p align="center">
  <a href="https://www.linkedin.com/in/drenfazlija">Dren Fazlija</a><sup>1</sup>,
  <a href="https://scholar.google.com/citations?user=Fv4Gf-wAAAAJ">Monty-Maximilian Zühlke</a><sup>1</sup>,
  <a href="https://www.linkedin.com/in/johanna-schrader-570558219/">Johanna Schrader</a><sup>1</sup>,
  <br>
  <a href="https://www.linkedin.com/in/arkadijorlov/">Arkadij Orlov</a><sup>2</sup>,
  <a href="https://www.linkedin.com/in/clara-stein-503061201/">Clara Stein</a><sup>1</sup>, 
  <a href="https://www.linkedin.com/in/olatunjiiyem/">Iyiola E. Olatunji</a><sup>3</sup>,
  <a href="https://www.linkedin.com/in/daniel-kudenko-8672583/">Daniel Kudenko</a><sup>1</sup>
  <br>
  <sup>1</sup>L3S Research Center
  <br>
  <sup>2</sup>E.ON Grid Solutions
  <br>
  <sup>3</sup>University of Luxembourg
</p>

<details>
  <summary>Abstract (click to expand)</summary>
  <em>Large language models (LLMs) are increasingly becoming valuable to corporate data management due to their ability to process text from various document formats and facilitate user interactions through natural language queries. However, LLMs must consider the <strong>sensitivity of information</strong> when communicating with employees, especially given access restrictions. Simple filtering based on user clearance levels can pose both performance and privacy challenges. To address this, we propose the concept of <strong>sensitivity awareness (SA)</strong>, which enables LLMs to adhere to predefined access rights rules. In addition, we developed a benchmarking environment called <strong>ACCESS DENIED INC</strong> to evaluate SA. Our experimental findings reveal significant variations in model behavior, particularly in managing unauthorized data requests while effectively addressing legitimate queries. This work establishes a foundation for benchmarking sensitivity-aware language models and provides insights to enhance privacy-centric AI systems in corporate environments.</em>
</details>

## Motivation of this Project
- **Unrestricted adversarial attacks** (e.g., simply changing an object's color) can fool state-of-the-art vision models even though the changes are obvious to humans – see below for some examples! 

<div align="center" style="margin-bottom: 0;">
  <!-- Row 1: Labels for Color-based Attack -->
  <div style="display: flex; justify-content: center; align-items: flex-end; margin-bottom: 0;">
    <div style="width:150px; margin:8px;"></div>
    <div style="width:450px; margin:8px; font-weight: bold; font-size: 16px; text-align: center;">Color-based Attack</div>
  </div>
  <!-- Row 2: Color-based Attack Images -->
  <div style="display: flex; justify-content: center; align-items: flex-end;">
    <div style="width:150px; margin:8px;"></div>
    <img src="project_page/semadv_140.JPEG" width="150" style="margin:8px;">
    <img src="project_page/cadv_140.png" width="150" style="margin:8px;">
    <img src="project_page/ncf_140.JPEG" width="150" style="margin:8px;">
  </div>
  <!-- Row 2: Names under Color-based Attack Images -->
  <div style="display: flex; justify-content: center; align-items: flex-start; margin-bottom: 8px;">
    <div style="width:150px; margin:8px;"></div>
    <div style="width:150px; margin:8px; text-align:center; font-size:13px; font-weight: bold">SemanticAdv</div>
    <div style="width:150px; margin:8px; text-align:center; font-size:13px; font-weight: bold">cAdv</div>
    <div style="width:150px; margin:8px; text-align:center; font-size:13px; font-weight: bold">NCF</div>
  </div>
  <!-- Row 3: Real Image Row -->
  <div style="display: flex; justify-content: center; align-items: flex-end;">
    <img src="project_page/real_140.JPEG" width="150" style="margin:8px;">
    <div style="width:150px; margin:8px;"></div>
    <div style="width:150px; margin:8px;"></div>
    <div style="width:150px; margin:8px;"></div>
  </div>
  <!-- Row 3: Name under Real Image -->
  <div style="display: flex; justify-content: center; align-items: flex-start; margin-bottom: 8px;">
    <div style="width:150px; margin:8px; text-align:center; font-size:13px; font-weight: bold;">Original</div>
    <div style="width:150px; margin:8px;"></div>
    <div style="width:150px; margin:8px;"></div>
    <div style="width:150px; margin:8px;"></div>
  </div>
  <!-- Row 4: Labels for Diffusion-based Attack -->
  <div style="display: flex; justify-content: center; align-items: flex-end; margin-bottom: 0;">
    <div style="width:150px; margin:8px;"></div>
    <div style="width:450px; margin:8px; font-weight: bold; font-size: 16px; text-align: center;">Diffusion-based Attack</div>
  </div>
  <!-- Row 5: Diffusion-based Attack Images -->
  <div style="display: flex; justify-content: center; align-items: flex-end;">
    <div style="width:150px; margin:8px;"></div>
    <img src="project_page/diffattack_140.JPEG" width="150" style="margin:8px;">
    <img src="project_page/advpp_140.png" width="150" style="margin:8px;">
    <img src="project_page/aca_140.JPEG" width="150" style="margin:8px;">
  </div>
  <!-- Row 5: Names under Diffusion-based Attack Images -->
  <div style="display: flex; justify-content: center; align-items: flex-start;">
    <div style="width:150px; margin:8px;"></div>
    <div style="width:150px; margin:8px; text-align:center; font-size:13px; font-weight: bold">DiffAttack</div>
    <div style="width:150px; margin:8px; text-align:center; font-size:13px; font-weight: bold">AdvPP</div>
    <div style="width:150px; margin:8px; text-align:center; font-size:13px; font-weight: bold">ACA</div>
  </div>
</div>



- Because these attacks aren't limited by traditional $\ell_p$-norm “imperceptibility” constraints, we **must involve people** to judge how convincing the images really are.

## Meet **SCOOTER** — *Systemizing Confusion Over Observations To Evaluate Realness*
- An **open-source, statistically powered** framework for human-in-the-loop evaluation of unrestricted adversarial images, making studies easier to run and results easier to compare.

## Key experimental findings
- **346 human participants vs. models**: three color-based attacks and three diffusion-based attacks all **failed** to produce images that humans find imperceptible.  
- **GPT-4o** can act as a first litmus test but it reliably flags only 4 / 6 attack types — **human evaluation is still essential**.

<p align="center">
  <img src="project_page/comparison.png" align="middle" width="600"/>
</p>

## What's inside the framework
- 🔬 **Best-practice playbook** for crowd studies: power analysis, fair compensation guidelines, and Likert-scale equivalence bounds for statistically solid results.  
- 🖥️ **Plug-and-play tooling**: a browser-based annotation template plus Python & R analysis scripts.  
- 🗂️ **Benchmark dataset**: 3 k genuine ImageNet photos, 7 k adversarial counterparts, and 34 k+ human ratings (all CC-BY).


## Take-home message
- Current automated vision defenses and detectors **do not align** with human perception.  
- **SCOOTER** provides the community with a **ground-truth benchmark** and ready-made tools to close that gap, accelerating research on truly “stealthy” attacks and genuinely robust models.
