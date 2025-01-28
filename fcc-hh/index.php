<?php
require('../config.php');

$layer = 'evt-type';
$acc = 'fcc-hh';
$evtType = 'none';
$fileType = 'none';
$campaign = 'none';
$det = 'none';
?>

<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>FCC-hh | FCC Physics Events</title>

    <link rel="icon" type="image/x-icon" href="<?= BASE_URL ?>/images/favicon.ico">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css"
          rel="stylesheet"
          integrity="sha384-T3c6CoIi6uLrA9TneNEoa7RxnatzjcDSCmG1MXxSR1GAsXEV/Dwwykc2MPK8M2HN"
          crossorigin="anonymous">
    <link rel="stylesheet"
          href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
    <link rel="stylesheet" href="<?= BASE_URL ?>/style/fcc.css">
  </head>

  <body>
    <?php include BASE_PATH . '/header.php'; ?>

    <article class="container-lg">
      <h1 class="mt-5">FCC-hh Samples</h1>

      <div class="list-group mt-3">
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/fcc-hh/LHEevents.php">Gen | Les Houches</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/fcc-hh/Delphesevents_fcc_v02.php">Delphes | v0.2</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/fcc-hh/Delphesevents_fcc_v03.php">Delphes | v0.3</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/fcc-hh/Delphesevents_fcc_v04.php">Delphes | v0.4</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/fcc-hh/Delphesevents_fcc_v05_scenarioI.php">Delphes | v0.5 scenario I.</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/fcc-hh/FCCsim_v03.php">Full Sim | v0.3</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/fcc-hh/FCCsim_v03_ecal.php">Full Sim | v0.3 ECal</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/fcc-hh/FCCsim_v04.php">Full Sim | v0.4</a>
      </div>

      <h2 class="mt-3">Delphes Card Reference</h2>

      <p>
        A repository for Delphes cards is available in the
        <a href="https://github.com/delphes/delphes/tree/master/card">GitHub repository</a>
        of the project, where example for many detector concepts exist.
      </p>

      <p>
        The Delphes cards used for the FCC-hh CDR and HL/HE-LHC yellow reports
        can be found here:
        <ul>
          <li>
            <a href="https://fccsw.web.cern.ch/fccsw/delphescards/download/delphes_cards_HL-HELHC_baseline.tgz">delphes_cards_HL-HELHC_baseline.tgz</a>
          </li>
          <li>
            <a href="https://fccsw.web.cern.ch/fccsw/delphescards/download/delphes_cards_FCChh_baseline.tgz">delphes_cards_FCChh_baseline.tgz</a>
          </li>
        </ul>
      </p>

      <p>
        Delphes cards for the most common solutions for future e+e- experiment
        detectors can be found at
        <a href="https://fccsw.web.cern.ch/fccsw/delphescards/">here</a> and
        they are also available on lxplus at
        <pre><code>/eos/project/f/fccsw-web/www/delphescards</code></pre>
        (where relevant cards are taken from the
        <a href="https://github.com/delphes/delphes/tree/master/cards">GitHub Delphes repository</a>).
      </p>
    </article>

    <?php include BASE_PATH . '/footer.php'; ?>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"
            integrity="sha384-C6RzsynM9kWDrMNeT87bh95OGNyZPhcTNXj1NW7RuBCsyN/o0jlpcV8Qyq46cDfL"
            crossorigin="anonymous"></script>
  </body>
</html>
