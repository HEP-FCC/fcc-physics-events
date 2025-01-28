<?php
require('../../../../config.php');

$layer = 'table';
$acc = 'fcc-ee';
$evtType = 'delphes';
$fileType = 'edm4hep-root';
$campaign = 'winter2023-training';
$det = 'idea-worse-hcalereso-cms';

$dataFilePath = BASE_PATH . '/data/FCCee/Delphesevents_winter2023_training_IDEA_worse_HCalEReso_CMS.txt';
$description = 'Delphes FCCee Physics events winter2023 training production (IDEA detector with worse HCal energy resolution &mdash; CMS like).';
?>

<?php require(BASE_PATH . '/fcc-ee/page.php') ?>
