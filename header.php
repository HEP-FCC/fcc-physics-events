    <header class="navbar navbar-expand-lg bg-blue sticky-top"
            data-bs-theme="light">
      <nav class="container-lg">
        <a class="navbar-brand" href="<?= BASE_URL ?>/index.php">
        <img src="<?= BASE_URL ?>/images/FCC-Logo_Short_RGB_White.png"
               alt="FCC Logo"
               height="36"
               class="d-inline-block align-text-top">
        </a>

        <button class="navbar-toggler"
                type="button"
                data-bs-toggle="collapse"
                data-bs-target="#navbarSupportedContent"
                aria-controls="navbarSupportedContent"
                aria-expanded="false"
                aria-label="Toggle navigation">
          <span class="navbar-toggler-icon"></span>
        </button>

        <div class="collapse navbar-collapse" id="navbarSupportedContent">
          <ul class="navbar-nav nav-pills me-auto mb-2 mb-lg-0">
            <?php if ($layer === 'top' || $acc === 'fcc-ee'): ?>
              <li class="nav-item">
                <a class="nav-link text-light<?php if ($acc === 'fcc-ee'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-ee">FCC-ee</a>
              </li>
            <?php endif ?>

            <?php if ($layer === 'top' || $acc === 'fcc-hh'): ?>
              <li class="nav-item">
                <a class="nav-link text-light<?php if ($acc === 'fcc-hh'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-hh">FCC-hh</a>
              </li>
            <?php endif ?>

            <!-- FCC-ee -->
            <?php if ($acc === 'fcc-ee'): ?>
              <!-- FCC-ee | Gen -->
              <?php if ($layer === 'evt-type' || $evtType === 'gen'): ?>
                <li class="nav-item">
                  <a class="ms-1 nav-link text-light<?php if ($evtType === 'gen'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-ee/gen">Gen</a>
                </li>
                <!-- FCC-ee | Gen | Les Houches -->
                <?php if ($layer === 'gen-type' || $fileType === 'lhe'): ?>
                  <li class="nav-item">
                    <a class="ms-1 nav-link text-light<?php if ($fileType === 'lhe'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-ee/gen/les-houches">Les Houches</a>
                  </li>
                <?php endif ?>
                <!-- FCC-ee | Gen | STDHEP -->
                <?php if ($layer === 'gen-type' || $fileType === 'stdhep'): ?>
                  <li class="nav-item">
                    <a class="ms-1 nav-link text-light<?php if ($fileType === 'stdhep'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-ee/gen/stdhep">STDHEP</a>
                  </li>
                <?php endif ?>
                <?php if ($fileType === 'stdhep'): ?>
                  <!-- FCC-ee | Gen | STDHEP | Winter 2023 -->
                  <li class="nav-item">
                    <a class="ms-1 nav-link text-light<?php if ($campaign === 'winter2023'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-ee/gen/stdhep/winter2023">Winter 2023</a>
                  </li>
                  <!-- FCC-ee | Gen | STDHEP | Winter 2023 --- training -->
                  <li class="nav-item">
                    <a class="ms-1 nav-link text-light<?php if ($campaign === 'winter2023-training'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-ee/gen/stdhep/winter2023_training">Winter 2023&ndash;training</a>
                  </li>
                  <!-- FCC-ee | Gen | STDHEP | Spring 2021 -->
                  <li class="nav-item">
                    <a class="ms-1 nav-link text-light<?php if ($campaign === 'spring2021'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-ee/gen/stdhep/spring2021">Spring 2021</a>
                  </li>
                <?php endif ?>
              <?php endif ?>

              <!-- FCC-ee | Delphes -->
              <?php if ($layer === 'evt-type' || $evtType === 'delphes'): ?>
                <li class="nav-item">
                  <a class="ms-1 nav-link text-light<?php if ($evtType === 'delphes'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-ee/delphes">Delphes</a>
                </li>
              <?php endif ?>
              <?php if ($evtType === 'delphes'): ?>
                <!-- FCC-ee | Delphes | Winter 2023 -->
                <?php if ($layer === 'campaign' || $campaign === 'winter2023'): ?>
                  <li class="nav-item">
                    <a class="ms-1 nav-link text-light<?php if ($campaign === 'winter2023'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-ee/delphes/winter2023">Winter 2023</a>
                  </li>
                <?php endif ?>
                <?php if ($campaign === 'winter2023'): ?>
                  <?php foreach($campaignDetectors['winter2023'] as $detector): ?>
                  <!-- FCC-ee | Delphes | Winter 2023 | <?= $detectorNames[$detector] ?> -->
                  <li class="nav-item">
                  <a class="ms-1 nav-link text-light<?php if ($det === $detector): ?> active bg-green<?php endif ?>"
                     href="<?= BASE_URL ?>/fcc-ee/delphes/winter2023/<?= $detector ?>"><?= $detectorNames[$detector] ?></a>
                  </li>
                  <?php endforeach ?>
                <?php endif ?>
                <!-- FCC-ee | Delphes | Winter 2023--training -->
                <?php if ($layer === 'campaign' || $campaign === 'winter2023-training'): ?>
                  <li class="nav-item">
                    <a class="ms-1 nav-link text-light<?php if ($campaign === 'winter2023-training'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-ee/delphes/winter2023-training">Winter 2023&ndash;training</a>
                  </li>
                <?php endif ?>
                <?php if ($campaign === 'winter2023-training'): ?>
                  <?php foreach($campaignDetectors['winter2023-training'] as $detector): ?>
                  <!-- FCC-ee | Delphes | Winter 2023--training | <?= $detectorNames[$detector] ?> -->
                  <li class="nav-item">
                  <a class="ms-1 nav-link text-light<?php if ($det === $detector): ?> active bg-green<?php endif ?>"
                     href="<?= BASE_URL ?>/fcc-ee/delphes/winter2023-training/<?= $detector ?>"><?= $detectorNames[$detector] ?></a>
                  </li>
                  <?php endforeach ?>
                <?php endif ?>
                <!-- FCC-ee | Delphes | Pre-fall 2022 -->
                <?php if ($layer === 'campaign' || $campaign === 'prefall2022'): ?>
                  <li class="nav-item">
                    <a class="ms-1 nav-link text-light<?php if ($campaign === 'prefall2022'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-ee/delphes/prefall2022/index.php">Pre-fall 2022</a>
                  </li>
                <?php endif ?>
                <?php if ($campaign === 'prefall2022'): ?>
                  <!-- FCC-ee | Delphes | Pre-fall 2022 | IDEA -->
                  <li class="nav-item">
                    <a class="ms-1 nav-link text-light<?php if ($det === 'idea'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-ee/delphes/prefall2022/idea">IDEA</a>
                  </li>
                <?php endif ?>
                <!-- FCC-ee | Delphes | Pre-fall 2022--training -->
                <?php if ($layer === 'campaign' || $campaign === 'prefall2022-training'): ?>
                  <li class="nav-item">
                    <a class="ms-1 nav-link text-light<?php if ($campaign === 'prefall2022-training'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-ee/delphes/prefall2022-training">Pre-fall 2022&ndash;training</a>
                  </li>
                <?php endif ?>
                <?php if ($campaign === 'prefall2022-training'): ?>
                  <!-- FCC-ee | Delphes | Pre-fall 2022--training | IDEA -->
                  <li class="nav-item">
                    <a class="ms-1 nav-link text-light<?php if ($det === 'idea'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-ee/delphes/prefall2022-training/idea">IDEA</a>
                  </li>
                <?php endif ?>
                <!-- FCC-ee | Delphes | Spring 2021 -->
                <?php if ($layer === 'campaign' || $campaign === 'spring2021'): ?>
                  <li class="nav-item">
                    <a class="ms-1 nav-link text-light<?php if ($campaign === 'spring2021'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-ee/delphes/spring2021">Spring 2021</a>
                  </li>
                <?php endif ?>
                <?php if ($campaign === 'spring2021'): ?>
                  <!-- FCC-ee | Delphes | Spring 2021 | IDEA -->
                  <li class="nav-item">
                    <a class="ms-1 nav-link text-light<?php if ($det === 'idea'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-ee/delphes/spring2021/idea">IDEA</a>
                  </li>
                  <!-- FCC-ee | Delphes | Spring 2021 | IDEA 3T -->
                  <li class="nav-item">
                    <a class="ms-1 nav-link text-light<?php if ($det === 'idea-3t'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-ee/delphes/spring2021/idea-3t">IDEA 3T</a>
                  </li>
                  <!-- FCC-ee | Delphes | Spring 2021 | IDEA Full Silicone -->
                  <li class="nav-item">
                    <a class="ms-1 nav-link text-light<?php if ($det === 'idea-fullsilicone'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-ee/delphes/spring2021/idea-fullsilicone">IDEA Full Silicone</a>
                  </li>
                <?php endif ?>
                <!-- FCC-ee | Delphes | Spring 2021--training -->
                <?php if ($layer === 'campaign' || $campaign === 'spring2021-training'): ?>
                  <li class="nav-item">
                    <a class="ms-1 nav-link text-light<?php if ($campaign === 'spring2021-training'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-ee/delphes/spring2021-training">Spring 2021&ndash;training</a>
                  </li>
                <?php endif ?>
                <?php if ($campaign === 'spring2021-training'): ?>
                  <!-- FCC-ee | Delphes | Spring 2021--training | IDEA -->
                  <li class="nav-item">
                    <a class="ms-1 nav-link text-light<?php if ($det === 'idea'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-ee/delphes/spring2021-training/idea">IDEA</a>
                  </li>
                <?php endif ?>
                <!-- FCC-ee | Delphes | Dev -->
                <?php if ($layer === 'campaign' || $campaign === 'dev'): ?>
                  <li class="nav-item">
                    <a class="ms-1 nav-link text-light<?php if ($campaign === 'dev'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-ee/delphes/dev">Dev</a>
                  </li>
                <?php endif ?>
                <?php if ($campaign === 'dev'): ?>
                  <!-- FCC-ee | Delphes | Dev | IDEA -->
                  <li class="nav-item">
                    <a class="ms-1 nav-link text-light<?php if ($det === 'idea'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-ee/delphes/dev/idea">IDEA</a>
                  </li>
                <?php endif ?>
              <?php endif ?>

              <!-- FCC-ee | Full Sim -->
              <?php if ($layer === 'evt-type' || $evtType === 'full-sim'): ?>
                <li class="nav-item">
                  <a class="ms-1 nav-link text-light<?php if ($evtType === 'full-sim'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-ee/full-sim/index.php">Full Sim</a>
                </li>
              <?php endif ?>
              <!-- FCC-ee | Full Sim | Devel -->
              <?php if ($evtType === 'full-sim'): ?>
                <li class="nav-item">
                  <a class="ms-1 nav-link text-light<?php if ($campaign === 'devel'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-ee/full-sim/devel/">Devel</a>
                </li>
              <?php endif ?>
            <?php endif ?>

            <!-- FCC-hh -->
            <?php if ($acc === 'fcc-hh'): ?>
            <!-- FCC-hh | Gen -->
            <?php if ($layer === 'evt-type' || $evtType === 'gen'): ?>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($evtType === 'gen'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-hh/gen/index.php">Gen</a>
            </li>
            <!-- FCC-hh | Gen | Les Houches -->
            <?php if ($layer === 'campaign' || $fileType === 'lhe'): ?>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($fileType === 'lhe'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-hh/LHEevents.php">Les Houches</a>
            </li>
            <?php endif ?>
            <?php endif ?>
            <!-- FCC-hh | Delphes -->
            <?php if ($layer === 'evt-type' || $evtType === 'delphes'): ?>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($evtType === 'delphes'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-hh/delphes/index.php">Delphes</a>
            </li>
            <!-- FCC-hh | Delphes | v02 -->
            <?php if ($layer === 'campaign' || $layer === 'table'): ?>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($campaign === 'fcc-v02'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-hh/Delphesevents_fcc_v02.php">v0.2</a>
            </li>
            <?php endif ?>
            <!-- FCC-hh | Delphes | v03 -->
            <?php if ($layer === 'campaign' || $layer === 'table'): ?>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($campaign === 'fcc-v03'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-hh/Delphesevents_fcc_v03.php">v0.3</a>
            </li>
            <?php endif ?>
            <!-- FCC-hh | Delphes | v04 -->
            <?php if ($layer === 'campaign' || $layer === 'table'): ?>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($campaign === 'fcc-v04'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-hh/Delphesevents_fcc_v04.php">v0.4</a>
            </li>
            <?php endif ?>
            <!-- FCC-hh | Delphes | v05_scenarioI -->
            <?php if ($layer === 'campaign' || $layer === 'table'): ?>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($campaign === 'fcc-v05-scenario-i'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-hh/Delphesevents_fcc_v05_scenarioI.php">v0.5 scenario I.</a>
            </li>
            <?php endif ?>
            <?php endif ?>
            <!-- FCC-hh | Full Sim -->
            <?php if ($layer === 'evt-type' || $evtType === 'full-sim'): ?>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($evtType === 'full-sim'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-hh/full-sim/index.php">Full Sim</a>
            </li>
            <!-- FCC-hh | Full Sim | v03 -->
            <?php if ($layer === 'campaign' || $layer === 'table'): ?>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($campaign === 'v03'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-hh/FCCsim_v03.php">v0.3</a>
            </li>
            <?php endif ?>
            <!-- FCC-hh | Full Sim | v03-ecal -->
            <?php if ($layer === 'campaign' || $layer === 'table'): ?>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($campaign === 'v03-ecal'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-hh/FCCsim_v03_ecal.php">v0.3 ECal</a>
            </li>
            <?php endif ?>
            <!-- FCC-hh | Full Sim | v04 -->
            <?php if ($layer === 'campaign' || $layer === 'table'): ?>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($campaign === 'v04'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/fcc-hh/FCCsim_v04.php">v0.4</a>
            </li>
            <?php endif ?>
            <?php endif ?>
            <?php endif ?>
          </ul>
          <ul class="navbar-nav nav-pills mb-auto mb-2 mb-lg-0">
            <li class="nav-item">
              <a class="nav-link text-light" href="#" data-bs-toggle="modal" data-bs-target="#aboutModal">About</a>
            </li>
          </ul>
        </div>
      </nav>
    </header>
