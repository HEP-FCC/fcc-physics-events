<?
ini_set('display_errors', '1');
error_reporting(E_ALL);
$debug=(isset($_GET["debug"])?$_GET["debug"]:false);
if(!isset($gobase)){$gobase="";}
?>
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>FCC Samples DB</title>

    <link rel="icon" type="image/x-icon" href="/fcc-physics-events/images/favicon.ico">
    <link rel="stylesheet" href="style/main.css">
  </head>

  <body>
    <?php include 'topbar.php'; ?>

    <h1>FCC Samples DB</h1>

    <p>This page describes FCC pre-generated samples for FCC-hh as well FCC-ee physics studies.</p>

    <h2>Production campaigns</h2>

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

    <footer>
      <p>Original creator: Clement Helsens &lt;<a href="mailto:clement.helsens@cern.ch">clement.helsens@cern.ch</a>&gt;</p>
    </footer>   
  </body>
</html>	
