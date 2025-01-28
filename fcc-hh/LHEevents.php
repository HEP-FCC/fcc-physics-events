<?php
require('../config.php');

$layer = 'table';
$acc = 'fcc-hh';
$evtType = 'gen';
$fileType = 'lhe';
$campaign = 'none';
$det = 'none';

$dataFilePath = BASE_PATH . '/data/FCChh/LHEevents.txt';

# $lname = array('No', 'Name', 'Nevents', 'Nfiles', 'Nbad', 'Neos', 'Size [GB]',
#                'Output Path', 'Main Process', 'Final States', 'Matching Param',
#                'Cross Section [pb]');

$description = '';
?>

<?php require(BASE_PATH . '/fcc-hh/page.php') ?>
