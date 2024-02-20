<?php
require('../../config.php');

$layer = 'table';
$acc = 'fcc-ee';
$det = 'idea-fullsilicon';
$evtType = 'delphes';
$prodTag = 'spring2021';
?>

<?php
$txt_file    = file_get_contents('../../data/FCCee/Delphesevents_spring2021_IDEA_FullSilicon.txt');

$lname=array('#','Name','Nevents','Nweights',
             'Nfiles','Nbad','Neos','Size (GB)',
             'Output Path','Main Process','Final States',
             'Cross Section (pb)','K-factor','Matching Eff.');

$descrition = 'Delphes FCCee Physic events spring 2021 production (IDEA with Track Covariance full matrix lower triangle)';
?>

<?php require('../page.php') ?>
