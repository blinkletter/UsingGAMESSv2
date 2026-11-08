# Fun With *GAMESS*

This resource is intended to help organic chemistry students set up the ***GAMESS*** computational chemistry software on their own computer and perform a series of small calculations. It supports my course in physical organic chemistry. There is another course available in computational chemistry that will take you much farther if you catch the bug here. I hear that that course is all math, but mine is all fun. Let us have some **fun with *GAMESS***.

```{figure} images/SN2_2_copy.gif
```

## Preface to the *Python* Edition

This book, Fun with GAMESS (*Python* edition), is an **update** of a previous web book, [Fun with GAMESS](https://blinkletter.github.io/UsingGAMESS). That work presented using the GAMESS system via a terminal emulator in a *Unix* system. That's still a good way to go, but to make things **more accessible** for students I have converted everything to *Python* in *Jupyter* notebooks. I used a LLM system to perform the conversion, and it did an amazing job. These pages are **adapted** from my own original work and I have included an AI statement at the bottom of each page to identify the contribution of the LLM (tl:dr it did all the *Python*). Students can explore simple computational chemistry examples using the hard-core terminal (party like its 1999!) or *Jupyter* notebooks (the future is here). Students must have a GAMESS executable file **installed on their own computer** to use these *Jupyter* notebooks. 

I **also** completely changed the exercises to run in the *Psi4* system. That new web book, [Fun with Psi4](https://blinkletter.github.io/UsingPsi4), is also available. It explores the **same examples** as this book, but uses the *Python* version of *Psi4*. This is a **better choice** for students because it will run via Google Colab and students will not need to install any software. However, *Psi4* was unable to successfully compute the examples in the final chapter, which explores calculations in solvent. So I am keeping the two GAMESS web books available, where the solvent calculations were possible.


# Table of Contents

Below is a list of the chapters in this book and some notes on what you will find in each.

[**1. Building Your System**](1_Setup.ipynb). Here you will be shown where to **obtain the software** and how to **install and run it** on a *MacOS Unix* system. These instructions should be easily applied to *Linux*. Essential ***Python* tools** for working with *GAMESS* files will be explained.

[**2. Water: Getting Started**](2_SmallMolecules.ipynb). This chapter will introduce how to **run a job** in *GAMESS*. We will explore the ways that molecules are described to *GAMESS* in **input files**. We will see examples of using *xyz* **Cartessian coordinates** to describe the locations of atoms, using symmetry point groups so that we need only describe the symmetry unique atoms and using internal coordinates via the ***Z-matrix***. We will optimize the structures of **water and ammonia** using *GAMESS*. We will use semi-empirical and *ab initio* methods and introduce the idea of **levels of theory** in calculations. *GAMESS* will be run from *Python* in a *Jupyter* notebook. Results will be interpretted using the **log files** generated as output from *GAMESS*.

[**3. Methane: Visual Input and Output**](3_Visual_Input.ipynb). Here we will see how to use the helper application ***MacMolPlt*** to build molecules and generate input files. We will run the *GAMESS* jobs from *Python* in the notebook. We will also use *MacMolPlt* to **analyze** the results and **visualize** structure, localize *bonding orbitals* and *molecular orbitals*. 

[**4. Ethane: Symmetry in Calculations**](4_Ethane.ipynb). Sometimes you want to explore the structure and energies of unstable systems, like transition states. We need to **constrain the optimization** to find a best structure in a high-energy situation. In this chapter we will explore the rotational **energy profile** of ethane using **symmetry point groups** to enforce the *anti* and the *eclipsed* conformations. We will calculate the energy for these two cases.

[**5. Butane: Rotation Energy Profiles**](5_Rotation_Profiles.ipynb). We can extend the idea of locking specific elements of a structure and performing a constrained optimization to explore the full **potential energy surface** for the rotation of the central C-C bond in butane. We will use **internal coordinates** to set values of for the torsion angle  and **constrain** that value using the \$STATPT IFREEZ option. We will also use ***Python*** to **build** a series of input files and **extract** the data from the result files. Interactive ***Python*** will be demonstrated for **analyzing and plotting** the data.


[**6. Allyl Cation * Benzene: &pi; Orbitals**](6_Pi_Orbitals.ipynb). We have already used simplified Hückel molecular orbital theory and interactive *Python* to calculate the &pi;-molecular orbitals for **conjugated systems**. Now let us demonstrate that goal with *GAMESS*. We will **calculate and visualize** the &pi;-molecular orbitals for the **allyl system** using *GAMESS* and *MacMolPlt*. We will revisit the idea of using **symmetry** in calculations.

[**7. Benzene: MOs \& Symmetry**](6_Benzene.ipynb). We will explore **more** about &pi;-molecular orbitals and aromaticity using benzene as an example. Along the way we will explore the symmetry builder tools in *MacMolPlt* in more detail and discuss some details of how symmetry affects the outcome of calculations.

[**8. Butadiene: Transition State for Rotation**](7_Butadiene.ipynb). We will use internal ***Z-matrix*** coordinates and *Python* to create a series of input files for **constrained optization** of different rotational conformers of butadiene. Interactive *Python* will be used to analyze and plot the results. Then we will explore **optimizing a transition state** structure for the highest energy point in the bond rotation. 

[**9. Diels-Alder Reaction: Intrinsic Reaction Coordinates**](8A_Diels_Alder.ipynb). We've all seen those little movies of a **reaction in progress**. We can make our own movies. We will use the Diels-Alder cycloaddition reaction as an example to demonstrate a **reaction coordinate scan** using a new method to **contrain coordinates**. We will not use the *Z-matrix*, but will use unique Cartessian coordinates and freeze automatically-generated internal coordinates of specific atoms using the \$ZMAT IFZMAT and FVALUE options. We can then use this system to generate a **series of structures** that may track near the **reaction coordinate**. From this series we will identify a structure that is near the transition state and perform a **transition state optimization**. Finally we will use the transition state as a starting point for following the potential energy surface down to the products on either side via an **intrinsic reaction coordinate** calculation. We will use *MacMolPlt* to assemble the complete reaction coordinate from the log files and **visualize** the structures. *MacMolPlt* will produce an **energy plot** for us. In the end, we will **make a movie**.

[**10. Solvent Models**](9_Solvent.ipynb). Organic chemists do not live in **gas phase**. Our reactions occur in **solvents**. *GAMESS* can include solvemnt effects through a variety of methods.  We will use the PCM method to **simulate a solvent environment** and observe the difference in calculations for an *S<sub>N</sub>2* reaction. We will again explore using **symmetry** to enforce geometry during optimization, **saddle point** optimization and **intrinsic reaction coordinate** calculations. This exercise will place an emphasis on using interactive *Python* tools to **process**, **clean** and **tabulate** the data. 

## Notes and Comments

**Style**. This book was started as notes to myself as I stumbled through **learning** how to use *GAMESS*. I wanted to build an exercise in visiualizing molecular orbitals but, as I realized how **easy** some calculations were, I decided to do **more**. Since it was written to me, by me, it has a casual and inconsistent **style**. You will see "I" and "we" mixed in with passive voice. I make no apologies. Feel free to **send me comments and corrections**. I do need an editor.

**Bold Text**. You will see many words in **bold face** fonts. I once took a course in student engagement and one recommendation was to intersperse bold **highlights** throughout a paragraph. This is apparently useful for helping students to **read**, especially now that we all have attention spans measured in **seconds** rather than **minutes**. I tried to keep the bold text on key words but often they are in patterns such as "**big**" and "**small**". In other places bold is used just because it had been a **while** since the last bold word. Please let me know if this **bold experiment** is helpful or annoying.

**Other Font Highlights**. There is a **code style** used throughout the book. It is rendered as a **monospace font** in red/pink when in a paragraph and as monospace font with a grey background when in blocks. It is used for code, text that is being quoted from text files, and for command line entries. **Italics** are used for the traditional scientific uses and also for filenames of applications such as *GAMESS*.

**Line Numbers**. Many code listings include line numbers along the **left edge**. These are generated by the book itself and are not part of the text of the original file. I use them to refer to **specific lines** in discussions and to **quickly find** the relevant locations in enormous text files. I do not use them in presentations of input files so that you can more easily use that code via cut-and-paste.

## AI Statement

This page is copied from the [original book](https://blinkletter.github.io/UsingGAMESS) with the help of Claude (Anthropic). The author's text is unchanged except that the chapter titles in the table of contents now link to the converted notebooks (for example `1_Setup.ipynb`) instead of markdown files, and the chapter 3 summary now says that jobs are run from *Python* rather than with *GamessQ*. The chapter summaries for chapters 1, 2, 5 and 8 now say *Python* where they said *Unix* tools or the terminal.
