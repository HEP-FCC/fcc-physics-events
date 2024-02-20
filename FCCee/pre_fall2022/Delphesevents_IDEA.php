<?php
require('../../config.php');

$layer = 'table';
$acc = 'fcc-ee';
$det = 'idea';
$evtType = 'delphes';
$prodTag = 'prefall2022';
?>

<?php
$txt_file    = file_get_contents('../../data/FCCee/Delphesevents_pre_fall2022_IDEA.txt');

$lname=array('#','Name','Nevents','Nweights',
             'Nfiles','Nbad','Neos','Size (GB)',
             'Output Path','Main Process','Final States',
             'Cross Section (pb)','K-factor','Matching Eff.');

$description = 'Delphes FCCee Physics events pre-fall 2022 production (IDEA with Track Covariance full matrix lower triangle).';
?>

<?php require('../page.php') ?>
