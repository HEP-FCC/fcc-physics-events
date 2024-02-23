<?php
require('../../config.php');

$layer = 'table';
$acc = 'fcc-ee';
$det = 'idea-3t';
$evtType = 'delphes';
$campaign = 'spring2021';
?>

<?php
$txt_file    = file_get_contents('../../data/FCCee/Delphesevents_spring2021_IDEA_3T.txt');

$lname=array('#','Name','Nevents','Nweights',
             'Nfiles','Nbad','Neos','Size (GB)',
             'Output Path','Main Process','Final States',
             'Cross Section (pb)','K-factor','Matching Eff.');

$description = 'Delphes FCCee Physics events Spring 2021 production (IDEA with Track Covariance full matrix lower triangle and 3T magnetic field).';
?>

<?php require('../page.php') ?>
