<?php
ini_set('display_errors', '1');
error_reporting(E_ALL);
$debug=(isset($_GET["debug"])?$_GET["debug"]:false);
if(!isset($gobase)){$gobase="";}

require('config.php');

$layer = 'top';
$acc = 'none';
$detector = 'none';
$evtType = 'none';
?>

<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>FCC Samples DB</title>

    <link rel="icon" type="image/x-icon" href="<?= BASE_URL ?>/images/favicon.ico">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css"
          rel="stylesheet"
          integrity="sha384-T3c6CoIi6uLrA9TneNEoa7RxnatzjcDSCmG1MXxSR1GAsXEV/Dwwykc2MPK8M2HN"
          crossorigin="anonymous">
    <link rel="stylesheet" href="<?= BASE_URL ?>/style/fcc.css">
  </head>

  <body data-bs-theme="light">
    <?php include 'header.php'; ?>

    <article class="container-lg mt-5">
      <h1>FCC Physics Events</h1>
      <p>Database of pre-generated samples for FCC-ee and FCC-hh performance studies.</p>

      <h2>Sections</h2>
      The site is divided into two sections:
      <ul>
        <li><a href="<?= BASE_URL ?>/FCCee/index.php">FCC-ee</a></li>
	<li><a href="<?= BASE_URL ?>/FCChh/index.php">FCC-hh</a></li>
      </ul>

      <h2 class="mt-5">Production campaigns</h2>

      <p>
        Exact <a href="https://cern.ch/key4hep/">Key4hep</a> stack used at the time of generation of the sample from the particular campaign can be found in the list below:
      </p>

      <ul>
        <li>
          <code>spring2021</code>
          <ul>
            <li>
              <code>/cvmfs/sw.hsf.org/spackages2/key4hep-stack/2021-05-12/x86_64-centos7-gcc8.3.0-opt/iyafnfo5muwvpbxcoa4ygwoxi2smkkwa/setup.sh</code>
            </li>
          </ul>
        </li>
        <li>
          <code>spring2021_training</code>
          <ul>
            <li>
              <code>/cvmfs/sw.hsf.org/spackages2/key4hep-stack/2021-05-12/x86_64-centos7-gcc8.3.0-opt/iyafnfo5muwvpbxcoa4ygwoxi2smkkwa/setup.sh</code>
            </li>
          </ul>
        </li>
        <li>
          <code>winter2023</code>
          <ul>
            <li>
              <code>/cvmfs/sw.hsf.org/spackages6/key4hep-stack/2022-12-23/x86_64-centos7-gcc11.2.0-opt/ll3gi/setup.sh</code>
            </li>
          </ul>
        </li>
        <li>
          <code>winter2023_training</code>
          <ul>
            <li>
              <code>/cvmfs/sw.hsf.org/spackages6/key4hep-stack/2022-12-23/x86_64-centos7-gcc11.2.0-opt/ll3gi/setup.sh</code>
            </li>
          </ul>
        </li>
      </ul>
    </article>

    <?php include 'footer.php'; ?>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"
	    integrity="sha384-C6RzsynM9kWDrMNeT87bh95OGNyZPhcTNXj1NW7RuBCsyN/o0jlpcV8Qyq46cDfL"
            crossorigin="anonymous"></script>
  </body>
</html>	
