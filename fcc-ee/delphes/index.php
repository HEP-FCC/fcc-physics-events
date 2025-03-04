<?php
require('../../config.php');

$layer = 'campaign';
$acc = 'fcc-ee';
$evtType = 'delphes';
$fileType = 'edm4hep-root';
$campaign = 'edm4hep-root';
$det = 'edm4hep-root';
?>

<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Delphes | FCC-ee | FCC Physics Events</title>

    <link rel="icon" type="image/x-icon" href="<?= BASE_URL ?>/images/favicon.ico">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css"
          rel="stylesheet"
          integrity="sha384-T3c6CoIi6uLrA9TneNEoa7RxnatzjcDSCmG1MXxSR1GAsXEV/Dwwykc2MPK8M2HN"
          crossorigin="anonymous">
    <link rel="stylesheet" href="<?= BASE_URL ?>/style/fcc.css">
  </head>

  <body>
    <?php include BASE_PATH . '/header.php'; ?>

    <article class="container-lg">
      <h1 class="mt-5">FCC-ee | Delphes Samples</h1>

      <div class="list-group mt-3">
        <?php foreach($campaignDetectors['winter2023'] as $detector): ?>
        <a class="list-group-item list-group-item-action"
           href="<?= BASE_URL ?>/fcc-ee/delphes/winter2023/<?= $detector ?>">Winter 2023 | <?= $detectorNames[$detector] ?></a>
        <?php endforeach ?>
      </div>

      <div class="list-group mt-1">
        <?php foreach($campaignDetectors['winter2023-training'] as $detector): ?>
        <a class="list-group-item list-group-item-action"
           href="<?= BASE_URL ?>/fcc-ee/delphes/winter2023-training/<?= $detector ?>">Winter 2023&ndash;training | <?= $detectorNames[$detector] ?></a>
        <?php endforeach ?>
      </div>

      <div class="list-group mt-1">
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/fcc-ee/delphes/prefall2022/idea">Pre-fall 2022 | IDEA</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/fcc-ee/delphes/prefall2022-training/idea">Pre-fall 2022&ndash;training | IDEA</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/fcc-ee/delphes/spring2021/idea">Spring 2021 | IDEA</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/fcc-ee/delphes/spring2021/idea-3t">Spring 2021 | IDEA 3T</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/fcc-ee/delphes/spring2021/idea-fullsilicone">Spring 2021 | IDEA Full Silicone</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/fcc-ee/delphes/spring2021-training/idea">Spring 2021&ndash;training | IDEA</a>
        <a class="list-group-item list-group-item-action" href="<?= BASE_URL ?>/fcc-ee/delphes/dev/idea">Dev | IDEA</a>
      </div>

      <?php include BASE_PATH . '/includes/k4h-stack.php'; ?>
    </article>

    <?php include BASE_PATH . '/footer.php'; ?>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"
            integrity="sha384-C6RzsynM9kWDrMNeT87bh95OGNyZPhcTNXj1NW7RuBCsyN/o0jlpcV8Qyq46cDfL"
            crossorigin="anonymous"></script>
  </body>
</html>
