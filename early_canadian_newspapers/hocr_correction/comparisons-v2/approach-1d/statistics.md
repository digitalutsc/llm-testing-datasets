# Overview
This document contains the analysis and statistics for the performance and accuracy of different models and thinking levels for the **HOCR Correction Script**.
> Note: After some experimentation, it can be concluded that temperature=0.0 works best for our problem and therefore, the results below use the same.

Default Sample Size: 5 Images (If different, it will be listed before the table)
> The statistics are averages across the 5 images and are NOT related.

## 2.5 Flash (Dynamic Thinking)
| Statistic | Value | 
|---|---|
| Execution Time | 21 mins |
| Total Errors found by human | 157 |
| AI Correctly Fixed | 74 |
| AI Missed (No change) | 30 |
| AI Wrong Fix (Hallucinated) | 15 |
| AI False Positives | 249 |      
| Accuracy on Errors | 69.65 |     


## 2.5 Flash (No Thinking)
| Statistic | Value | 
|---|---|
| Execution Time | 6 mins 45 seconds |
| Total Errors found by human | 119 |
| AI Correctly Fixed | 75 |
| AI Missed (No change) | 26 |
| AI Wrong Fix (Hallucinated) | 18 |
| AI False Positives | 453 |      
| Accuracy on Errors | 68.39 |  


## 3 Flash (Minimal Thinking)
| Statistic | Value | 
|---|---|
| Execution Time | 8 mins |
| Total Errors found by human | 119 |
| AI Correctly Fixed | 79 |
| AI Missed (No change) | 20 |
| AI Wrong Fix (Hallucinated) | 20 |
| AI False Positives | 554 |      
| Accuracy on Errors | 71.52 |  


## 3 Flash (Low Thinking)
> This model and thinking combination only generated HOCR files for 2 images.

| Statistic | Value | 
|---|---|
| Execution Time | 9 mins 30 seconds |
| Total Errors found by human | 154 |
| AI Correctly Fixed | 3 |
| AI Missed (No change) | 149 |
| AI Wrong Fix (Hallucinated) | 2 |
| AI False Positives | 17 |      
| Accuracy on Errors | 2.73 |  

## 3 Flash (Medium Thinking)
| Statistic | Value | 
|---|---|
| Execution Time | 29 mins |
| Total Errors found by human | 119 |
| AI Correctly Fixed | 74 |
| AI Missed (No change) | 36 |
| AI Wrong Fix (Hallucinated) | 9 |
| AI False Positives | 218 |      
| Accuracy on Errors | 66.73 |  

## 3.1 Pro (Low Thinking)
> This model and thinking combination only generated HOCR files for 4 images.

| Statistic | Value | 
|---|---|
| Execution Time | 20 mins 30 seconds |
| Total Errors found by human | 94 |
| AI Correctly Fixed | 77 |
| AI Missed (No change) | 8 |
| AI Wrong Fix (Hallucinated) | 10 |
| AI False Positives | 542 |      
| Accuracy on Errors | 76.22 |  
