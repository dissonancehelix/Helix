This dataset contains MRI, fMRI, and behavioral data acquired from 26 healthy volunteers (ages 19–34) undergoing graded propofol sedation. Participants performed mental imagery tasks (tennis, spatial navigation, hand squeeze) and a motor response task across varying levels of sedation, including periods of behavioral unresponsiveness.

Data Contents
Raw data: Anatomical T1w scans and six BOLD runs per subject (four task-based, two resting-state), organized in BIDS format.
Derivatives:
fMRIPrep outputs (preprocessing)
XCP-D outputs (denoising, functional connectivity, ALFF, ReHo)
MRIQC outputs (quality metrics)
FreeSurfer reconstructions
Behavioral: Hand-squeeze force recordings, task events, propofol effect-site concentrations.
QC reports: Subject-level .html reports for preprocessing and denoising.

Preprocessing
All functional and anatomical data were preprocessed using fMRIPrep (v23.2.1). Denoising was performed with XCP-D (v0.10.6), providing multiple pipelines (with/without global signal regression; band-pass or high-pass filtering).

When reusing this dataset, please cite the following publications derived from these data:
Huang, Z. et al. Brain imaging reveals covert consciousness during behavioral unresponsiveness induced by propofol. Sci Rep 8, 13195 (2018).
Huang, Z. et al. Anterior insula regulates brain network transitions that gate conscious access. Cell Rep 35, 109081 (2021).
Huang, Z. et al. Asymmetric neural dynamics characterize loss and recovery of consciousness. Neuroimage 236, 118042 (2021).