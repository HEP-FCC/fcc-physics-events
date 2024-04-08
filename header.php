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
              <a class="nav-link text-light<?php if ($acc === 'fcc-ee'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/FCCee/index.php">FCC-ee</a>
            </li>
            <?php endif ?>

            <?php if ($layer === 'top' || $acc === 'fcc-hh'): ?>
            <li class="nav-item">
              <a class="nav-link text-light<?php if ($acc === 'fcc-hh'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/FCChh/index.php">FCC-hh</a>
            </li>
            <?php endif ?>

            <?php if ($acc === 'fcc-ee'): ?>
            <?php if ($layer === 'evt-type' || $evtType === 'lhe'): ?>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($evtType === 'lhe'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/FCCee/LHEevents.php">Les Houches</a>
            </li>
            <?php endif ?>
            <?php if ($layer === 'evt-type' || $evtType === 'stdhep'): ?>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($evtType === 'stdhep'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/FCCee/stdhep/index.php">STDHEP</a>
            </li>
            <?php endif ?>
            <?php if ($evtType === 'stdhep'): ?>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($campaign === 'winter2023'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/FCCee/stdhep/winter2023">Winter 2023</a>
            </li>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($campaign === 'winter2023-training'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/FCCee/stdhep/winter2023_training">Winter 2023 &ndash; training</a>
            </li>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($campaign === 'spring2021'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/FCCee/stdhep/spring2021">Spring 2021</a>
            </li>
            <?php endif ?>
            <?php if ($layer === 'evt-type' || $evtType === 'delphes'): ?>
            <li class="ms-1 nav-item dropdown">
              <a class="nav-link dropdown-toggle text-light<?php if ($evtType === 'delphes'): ?> active bg-green<?php endif ?>"
                 href="#"
                 role="button"
                 data-bs-toggle="dropdown"
                 aria-expanded="false">Delphes</a>
              <ul class="dropdown-menu">
                <li><a class="dropdown-item" href="<?= BASE_URL ?>/FCCee/winter2023/index.php">Winter 2023</a>
                <li><a class="dropdown-item" href="<?= BASE_URL ?>/FCCee/winter2023_training/index.php">Winter 2023 &ndash; training</a>
                <li><a class="dropdown-item" href="<?= BASE_URL ?>/FCCee/pre_fall2022/index.php">Pre-fall 2022</a>
                <li><a class="dropdown-item" href="<?= BASE_URL ?>/FCCee/pre_fall2022_training/index.php">Pre-fall 2022 &ndash; training</a>
                <li><a class="dropdown-item" href="<?= BASE_URL ?>/FCCee/spring2021/index.php">Spring 2021</a></li>
                <li><a class="dropdown-item" href="<?= BASE_URL ?>/FCCee/spring2021_training/index.php">Spring 2021 &ndash; training</a>
                <li><a class="dropdown-item" href="<?= BASE_URL ?>/FCCee/dev/index.php">Dev</a>
              </ul>
            </li>
            <?php if ($evtType === 'delphes'): ?>
            <?php if ($campaign === 'winter2023'): ?>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($det === 'idea'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/FCCee/winter2023/Delphesevents_IDEA.php">IDEA</a>
            </li>
            <?php endif ?>
            <?php if ($campaign === 'winter2023-training'): ?>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($det === 'idea'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/FCCee/winter2023_training/Delphesevents_IDEA.php">IDEA</a>
            </li>
            <?php endif ?>
            <?php if ($campaign === 'prefall2022'): ?>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($det === 'idea'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/FCCee/pre_fall2022/Delphesevents_IDEA.php">IDEA</a>
            </li>
            <?php endif ?>
            <?php if ($campaign === 'prefall2022-training'): ?>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($det === 'idea'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/FCCee/pre_fall2022_training/Delphesevents_IDEA.php">IDEA</a>
            </li>
            <?php endif ?>
            <?php if ($campaign === 'spring2021'): ?>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($det === 'idea'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/FCCee/spring2021/Delphesevents_IDEA.php">IDEA</a>
            </li>
            <?php endif ?>
            <?php if ($campaign === 'spring2021-training'): ?>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($det === 'idea'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/FCCee/spring2021_training/Delphesevents_IDEA.php">IDEA</a>
            </li>
            <?php endif ?>
            <?php if ($campaign === 'dev'): ?>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($det === 'idea'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/FCCee/dev/Delphesevents_IDEA.php">IDEA</a>
            </li>
            <?php endif ?>
            <?php if ($campaign === 'spring2021'): ?>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($det === 'idea-3t'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/FCCee/spring2021/Delphesevents_IDEA_3T.php">IDEA 3T</a>
            </li>
            <?php endif ?>
            <?php if ($campaign === 'spring2021'): ?>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($det === 'idea-fullsilicon'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/FCCee/spring2021/Delphesevents_IDEA_FullSilicon.php">IDEA Full Silicon</a>
            </li>
            <?php endif ?>
            <?php endif ?>
            <?php endif ?>
            <?php if ($layer === 'evt-type' || $evtType === 'full-sim'): ?>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($evtType === 'full-sim'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/FCCee/full-sim/index.php">Full Sim</a>
            </li>
            <?php endif ?>
            <?php endif ?>

            <!-- FCC-hh -->
            <?php if ($acc === 'fcc-hh'): ?>
            <!-- FCC-hh | Gen -->
            <?php if ($layer === 'evt-type' || $evtType === 'gen'): ?>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($evtType === 'gen'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/FCChh/gen/index.php">Gen</a>
            </li>
            <!-- FCC-hh | Gen | Les Houches -->
            <?php if ($layer === 'campaign' || $campaign === 'lhe'): ?>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($campaign === 'lhe'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/FCChh/LHEevents.php">Les Houches</a>
            </li>
            <?php endif ?>
            <?php endif ?>
            <!-- FCC-hh | Delphes -->
            <?php if ($layer === 'evt-type' || $evtType === 'delphes'): ?>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($evtType === 'delphes'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/FCChh/delphes/index.php">Delphes</a>
            </li>
            <!-- FCC-hh | Delphes | v02 -->
            <?php if ($layer === 'campaign' || $layer === 'table'): ?>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($campaign === 'v02'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/FCChh/Delphesevents_fcc_v02.php">v0.2</a>
            </li>
            <?php endif ?>
            <!-- FCC-hh | Delphes | v03 -->
            <?php if ($layer === 'campaign' || $layer === 'table'): ?>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($campaign === 'v03'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/FCChh/Delphesevents_fcc_v03.php">v0.3</a>
            </li>
            <?php endif ?>
            <!-- FCC-hh | Delphes | v04 -->
            <?php if ($layer === 'campaign' || $layer === 'table'): ?>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($campaign === 'v04'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/FCChh/Delphesevents_fcc_v04.php">v0.4</a>
            </li>
            <?php endif ?>
            <?php endif ?>
            <!-- FCC-hh | Full Sim -->
            <?php if ($layer === 'evt-type' || $evtType === 'full-sim'): ?>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($evtType === 'full-sim'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/FCChh/full-sim/index.php">Full Sim</a>
            </li>
            <!-- FCC-hh | Full Sim | v03 -->
            <?php if ($layer === 'campaign' || $layer === 'table'): ?>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($campaign === 'v03'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/FCChh/FCCsim_v03.php">v0.3</a>
            </li>
            <?php endif ?>
            <!-- FCC-hh | Full Sim | v03-ecal -->
            <?php if ($layer === 'campaign' || $layer === 'table'): ?>
            <li class="nav-item">
              <a class="ms-1 nav-link text-light<?php if ($campaign === 'v03-ecal'): ?> active bg-green<?php endif ?>" href="<?= BASE_URL ?>/FCChh/FCCsim_v03_ecal.php">v0.3 ECal</a>
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
