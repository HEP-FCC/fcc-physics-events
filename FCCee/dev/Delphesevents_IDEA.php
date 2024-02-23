<?php
require('../../config.php');

$layer = 'table';
$acc = 'fcc-ee';
$det = 'idea';
$evtType = 'delphes';
$campaign = 'dev';
?>

<?php
$txt_file    = file_get_contents('../../data/FCCee/Delphesevents_dev_IDEA.txt');

$lname=array('#','Name','Nevents','Nweights',
             'Nfiles','Nbad','Neos','Size (GB)',
             'Output Path','Main Process','Final States',
             'Cross Section (pb)','K-factor','Matching Eff.');

$description = 'Delphes FCCee Physic events dev production (IDEA with Track Covariance full matrix lower triangle).';
?>

<?php require('../page.php') ?>
