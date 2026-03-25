# ChemClaw Skills Catalog

本文件用于管理 ChemClaw 的技能分类与建设清单。

## Skills Table

| 编号 | 大类 | Name | Description | 状态 |
|---|---|---|---|---|
| 1 | **Knowledge Mining** |  | 将文献、图表和反应信息转换为结构化化学知识。 |  |
| 1.1 | ↳ | `literature-parsing` | PDF 文献转 Markdown，并提取图表图片。 | ✅ 已完成 |
| 1.2 | ↳ | `reaction-data-extraction` | 从文献提取反应物、条件、产率并输出结构化数据。 | ✅ 已完成 |
| 1.3 | ↳ | `compound-characterization-extraction` |  | ⬜ 待建设 |
| 1.4 | ↳ | `computational-molecular-structure-extraction` |  | ⬜ 待建设 |
| 2 | **Chemical Representation** |  | 在 IUPAC、SMILES、图像等分子表示之间进行转换。 |  |
| 2.1 | ↳ | `iupac-to-smiles` | 将 IUPAC 名称转换为 SMILES（OPSIN）。 | ✅ 已完成 |
| 2.2 | ↳ | `smiles-to-iupac` | 将 SMILES 转换为 IUPAC 名称（多方法回退）。 | ✅ 已完成 |
| 2.3 | ↳ | `mol-image-to-smiles` | 分子结构图片识别为 SMILES（DECIMER/MolNextR）。 | ✅ 已完成 |
| 3 | **Prediction Engines** |  | 基于分子表示进行性质与谱学相关预测。 |  |
| 3.1 | ↳ | `adme-prediction` | 预测分子 ADME 性质（如 Caco-2、HIA、Pgp、生物利用度、亲脂性）。 | ✅ 已完成 |
| 3.2 | ↳ | `pka-prediction` |  | ⬜ 待建设 |
| 3.3 | ↳ | `et30-prediction` |  | ⬜ 待建设 |
| 3.4 | ↳ | `melting-point-prediction` |  | ⬜ 待建设 |
| 3.5 | ↳ | `boiling-point-prediction` |  | ⬜ 待建设 |
| 3.6 | ↳ | `ch-nmr-prediction` |  | ⬜ 待建设 |
| 3.7 | ↳ | `b-nmr-prediction` |  | ⬜ 待建设 |
| 3.8 | ↳ | `p-nmr-prediction` |  | ⬜ 待建设 |
| 3.9 | ↳ | `f-nmr-prediction` |  | ⬜ 待建设 |
| 3.10 | ↳ | `si-nmr-prediction` |  | ⬜ 待建设 |
| 3.11 | ↳ | `ir-prediction` |  | ⬜ 待建设 |
| 3.12 | ↳ | `raman-prediction` |  | ⬜ 待建设 |
| 3.13 | ↳ | `surface-tension-prediction` |  | ⬜ 待建设 |
| 3.14 | ↳ | `viscosity-prediction` |  | ⬜ 待建设 |
| 3.15 | ↳ | `tlc-rf-prediction` |  | ⬜ 待建设 |
| 3.16 | ↳ | `chiral-separation-prediction` |  | ⬜ 待建设 |
| 4 | **Reaction Intelligence** |  | 围绕反应结果、条件和选择性进行推断与优化。 |  |
| 4.1 | ↳ | `reaction-outcome-prediction` |  | ⬜ 待建设 |
| 4.2 | ↳ | `reaction-condition-optimization` |  | ⬜ 待建设 |
| 5 | **Computational Chemistry** |  | 提供计算化学流程与文件处理能力。 |  |
| 5.1 | ↳ | `geometry-optimization` |  | ⬜ 待建设 |
| 5.2 | ↳ | `chemical-file-converter` | 支持 `.xyz/.gjf/.mol/.sdf/.pdb/.mol2` 等格式互转。 | ✅ 已完成 |
| 6 | **Experiment Intelligence** |  | 提供实验方案与实验执行辅助。 |  |
| 6.1 | ↳ | `experimental-protocol-generation` |  | ⬜ 待建设 |
| 7 | **Scientific Writing** |  | 支持科研写作、综述与论文段落生成。 |  |
| 7.1 | ↳ | `paper-section-generation` |  | ⬜ 待建设 |
| 7.2 | ↳ | `literature-review-writing` |  | ⬜ 待建设 |
| 8 | **Visualization** |  | 提供分子结构与论文级图形可视化。 |  |
| 8.1 | ↳ | `mol-2d-viewer` | SMILES/化学名称转 2D 结构图。 | ✅ 已完成 |
| 8.2 | ↳ | `mol-3d-viewer` | SMILES/化学名称转 3D 结构并可导出交互网页。 | ✅ 已完成 |
| 8.3 | ↳ | `mol-paper-renderer` | 论文级分子渲染，输出 SVG/PNG/PDF/GIF。 | ✅ 已完成 |
