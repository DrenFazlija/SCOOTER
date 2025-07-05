# Data Processing

## Reassessed ImageNet-Labels
Out of the 50,000 ImageNet validation images, we only keep images that resemble *exactly* one ImageNet class. [Research by Google](https://arxiv.org/abs/2006.07159) demonstrated that many ImageNet instances depict multiple ImageNet objects at once or none. Both cases are suboptimal: Whereas images with no correct solution are useless for evaluating ImageNet models, depicting multiple ImageNet objects makes evaluating adversarial examples quite tricky. 

For example, an image may depict both a snowmobile (class 802) and a snowplow (class 803), but it is only labeled with one correct label (let's say 802). Would a modified instance of this image, which the model now classifies as class 803, be a legitimate adversarial example? Our opinion: **No**. Hence, we should use Google's [reassessed ImageNet labels](https://arxiv.org/abs/2006.07159) to remove such ambiguous data points, which leaves us with ***39,394*** remaining images.

## Ensemble of Target Models

To simplify consecutive manual portions of the data processing, we initially only keep images that are easily correctly classified (i.e., with high confidence) by a set of computer vision models. We decided to consider the predictions of three different ResNet-50 models: (i) the pre-trained ResNet-50 model [as provided by the Timm package](https://huggingface.co/docs/timm/models/resnet) and the most robust ResNet-50 models of [RobustBench](https://robustbench.github.io/) against (ii) norm-based ImageNet attacks ([Salman et al., 2020](https://arxiv.org/abs/2007.08489)) and (iii) corruption-based ImageNet attacks ([Erichson et al., 2022](https://arxiv.org/abs/2202.01263)). This ensemble gives us a more unified set of images.

1. We keep images that all three models correctly classify.
2. From these "shared easy images," we pick out the five images with the highest prediction confidence of a model for each of the 1,000 classes.

This process should generally leave us with 5,000 images per model. However, some classes have less than five images that all three models classify correctly.

## Getting Clean Top-3 Images of a Target Model

As described above, each model should have (up to) five images per class, which are generally easy to predict for said model. However, within SCOOTER, we are only interested in images that do not depict modifications themselves! This is quite the issue with ImageNet, as many of the scraped images contain modifications such as watermarks, filters, or visible noise. Hence, we have to filter out unsuitable images ***manually***.

Our **goal** is to have **three images for each class** by the end of the data processing.

### From Top-5 to Top-3
We tried to ensure that most classes only contained images from a model's initial Top-5 while ensuring that none looked visibly modified. Our removal strategy can be described as follows:

1. If the three easiest images contain no visible modifications: Remove the remaining two instances.
2. If the class includes an assortment of three clean Top-3 and Top-5 instances: Keep the three clean images and remove the two modified instances.
3. If the previous two cases are not fulfilled, we have at least three visibly modified images!
    
    3.1. Keep any of the images whose modifications can be removed by simply cropping them (e.g., an image with a watermark in the bottom right corner). **Important:** After cropping the initial image, the class object must remain fully visible.

    3.2. Every other image that could not be "saved" must be removed!

### Additional Images
Unfortunately, some classes contained more than three unsalvageable ImageNet instances that we had to remove. We fill the affected classes with additional clean images outside of the Top-5 for these classes. Please keep the following in mind:

1. Some classes already contained less than three images correctly classified by the entire ensemble. Therefore, we only considered images correctly classified by the target model at hand (generally a larger image pool).
2. We still prioritized high-confidence instances when choosing new images for each class.
3. However, we wanted to avoid any modifications (even non-invasive cropping) when choosing images. For example, we preferred low-confidence instances that required no cropping to high-confidence images that required further changes. Only if there were not enough clean images in the larger image pool did we decide to add cropped images to the final dataset.

The above process should leave us with 3,000 clean images per model.