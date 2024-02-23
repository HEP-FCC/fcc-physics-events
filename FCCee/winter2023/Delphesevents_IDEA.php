<?php
require('../../config.php');

$layer = 'table';
$acc = 'fcc-ee';
$det = 'idea';
$evtType = 'delphes';
$campaign = 'winter2023';
?>

<?php
$txt_file    = file_get_contents('../../data/FCCee/Delphesevents_winter2023_IDEA.txt');

$lname=array('#','Name','Nevents','Nweights',
             'Nfiles','Nbad','Neos','Size (GB)',
             'Output Path','Main Process','Final States',
             'Cross Section (pb)','K-factor','Matching Eff.');

$description = 'Delphes FCCee Physics events winter2023 production (IDEA Detector).';
?>

<?php require('../page.php') ?>
