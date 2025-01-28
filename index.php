<?php
require('config.php');

$layer = 'top';
$acc = 'none';
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
    <title>FCC Physics Events</title>

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
    <?php include 'header.php'; ?>

    <article class="container-lg mt-5">
      <h1>FCC Physics Events</h1>

      <p class="mt-3">
        Database of centrally produced pre-generated samples for
        <a href="https://hep-fcc.github.io/FCChhPhysicsPerformance/"
           target="_blank">FCC-hh</a>&nbsp;<i class="bi bi-box-arrow-up-right"
                                              style="font-size: 12px; color: darkred;"></i>
        and
        <a href="https://hep-fcc.github.io/FCCeePhysicsPerformance/"
           target="_blank">FCC-ee</a>&nbsp;<i class="bi bi-box-arrow-up-right"
                                              style="font-size: 12px; color: darkred;"></i>
        physics performance studies.
      </p>

      <p>
        More information about how the samples were produced can be found in
        the <a href="https://github.com/HEP-FCC/FCC-config"
               target="_blank">FCC-config</a>&nbsp;<i class="bi bi-box-arrow-up-right"
                                                      style="font-size: 12px; color: darkred;"></i> repository.
      </p>

      <h2 class="mt-3">Accelerators</h2>
      The FCC integrated program includes two accelerator proposals:
      <div class="list-group mt-3">
        <a class="list-group-item list-group-item-action"
           href="<?= BASE_URL ?>/fcc-ee/index.php">FCC-ee</i></a>
        <a class="list-group-item list-group-item-action"
           href="<?= BASE_URL ?>/fcc-hh/index.php">FCC-hh</a>
      </div>
    </article>

    <?php include 'footer.php'; ?>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"
            integrity="sha384-C6RzsynM9kWDrMNeT87bh95OGNyZPhcTNXj1NW7RuBCsyN/o0jlpcV8Qyq46cDfL"
            crossorigin="anonymous"></script>
  </body>
</html>
