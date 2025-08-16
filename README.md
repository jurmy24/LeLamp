# LeLamp

![LeLamp Banner](./docs/assets/images/README/Banner.png)

An open source robot lamp based on [Apple's Elegnt](https://machinelearning.apple.com/research/elegnt-expressive-functional-movement), made by [[Human Computer Lab]](https://www.humancomputerlab.com/)

**This repository is an early work in progress.** We published our progress early on as we believe early feedback leads to better design iteration. To contribute ideas, you're welcome to join our [Discord](https://discord.gg/4hmNW3Ep).

# How to build LeLamp

![](./docs/assets/images/README/lelamp_irl.jpg)

## Bill Of Materials

You can find the Bill Of Materials for LeLamp [here](https://docs.google.com/spreadsheets/d/1C50qqSxJjCHEnh6j_Dcfx8JzyLlGobKSOYA0ePJUDVk/edit?gid=25686295#gid=25686295).

The most critical component of LeLamp is the servos and the servo driver. You can create a minimal version of LeLamp with only these 2 components. However, you won't be extend the functionalities of the lamp more than movement.

Note: We know that sourcing these components from our source might be hard. You can find equivalent of them in your region. If you do find the sources and would like to contribute, we'd be glad to include your BOM in this repository for your region.

## 3D Prints

![](./docs/assets/images/1_lamp_3d.png)

You can find 3D prints file for LeLamp in `/3D/`. A guide on how many you have to print and what design to print can be found in `/docs/1. Schematics.md`.

Furthermore, you can find the OnShape of LeLamp [here](https://cad.onshape.com/documents/16c9706360b5ad34f9c8db49/w/2edfa54c83253c120fbc9e58/e/a7196194821d9cfe2842a44a).

## Assembly

For assembly of LeLamp, we have listed the steps in `/docs/`. There are 5 sections:

1. **Schematics**: Components and 3D parts.
2. **Servos**: How to set up servos.
3. **Lamp Head**: How to assemble and test the lamp head.
4. **Lamp Body**: How to assemble the lamp body.
5. **Lamp Control**: How to control the lamp.

# How to run LeLamp

For lamp control, please refer to the [**LeLamp Runtime's Github**](https://github.com/humancomputerlab/lelamp_runtime).

# License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.
