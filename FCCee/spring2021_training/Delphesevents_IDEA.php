<?php
require('../../config.php');

$layer = 'table';
$acc = 'fcc-ee';
$det = 'idea';
$evtType = 'delphes';
$campaign = 'spring2021-training';
?>

<?php
$txt_file    = file_get_contents('../../data/FCCee/Delphesevents_spring2021_training_IDEA.txt');

$lname=array('#','Name','Nevents','Nweights',
             'Nfiles','Nbad','Neos','Size (GB)',
             'Output Path','Main Process','Final States',
             'Cross Section (pb)','K-factor','Matching Eff.');

$description = 'Delphes FCCee Physic events Spring 2021 &ndash; training  production (IDEA with Track Covariance full matrix lower triangle).';
?>

<?php require('../page.php') ?>
