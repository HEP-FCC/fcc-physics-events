<?php
require('../config.php');

$layer = 'table';
$acc = 'fcc-hh';
$evtType = 'gen';
$campaign = 'lhe';
?>

<?php
$txt_file = file_get_contents(BASE_PATH . '/data/FCChh/LHEevents.txt');

$lname = array('No', 'Name', 'Nevents', 'Nfiles', 'Nbad', 'Neos', 'Size [GB]',
               'Output Path', 'Main Process', 'Final States', 'Matching Param',
               'Cross Section [pb]');

$description = '';
?>

<?php require(BASE_PATH . '/FCChh/page.php') ?>
