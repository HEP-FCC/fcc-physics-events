<?php
require('../../config.php');

$layer = 'table';
$acc = 'fcc-ee';
$det = 'idea';
$evtType = 'delphes';
$prodTag = 'winter2023-training';
?>

<?php
$txt_file    = file_get_contents('../../data/FCCee/Delphesevents_winter2023_training_IDEA.txt');

$lname=array('#','Name','Nevents','Nweights',
             'Nfiles','Nbad','Neos','Size (GB)',
             'Output Path','Main Process','Final States',
             'Cross Section (pb)','K-factor','Matching Eff.');

$description = 'Delphes FCCee Physics events winter2023 training production (IDEA Detector).';
?>

<?php require('../page.php') ?>
