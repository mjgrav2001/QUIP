#!/bin/bash
#PREDICATE: QUIP_MAKEFILE["HAVE_CP2K"] == 1

set -e

if [ -z $QUIP_ROOT ]; then
   echo "$0: Need QUIP_ROOT defined"
   exit 1
fi
if [ -z $QUIP_ARCH ]; then
   echo "$0: Need QUIP_ARCH defined"
   exit 1
fi

mydir=`dirname $0`
bindir=$mydir/../build/$QUIP_ARCH

if [ ! -x $bindir/cp2k_driver ]; then
   (cd $QUIP_ROOT && make FilePot_drivers) || exit 2
fi

TEST=test_cp2k_driver.sh

cat<<EOF_LIB > $TEST.all_res.CHARMM.lib
%residue H2O1 TIP3 WAT
   0    8   2   3   0   0   0   0   OT    -0.834   OT  
   0    1   1   0   0   0   0   0   HT     0.417   HT  
   0    1   1   0   0   0   0   0   HT     0.417   HT  
EOF_LIB

cat<<EOF_IN > $TEST.in.xyz
6
Lattice="10.0 0.0 0.0  0.0 10.0 0.0   0.0 0.0 10.0"  Properties=species:S:1:pos:R:3 Library=$TEST.all_res.CHARMM.lib
H 0.87 -0.166666667 -2.0
O 0.0 0.333333333 -2.0
H -0.87 -0.166666667 -2.0
O -0.33333333 0.0 2.0
H 0.16666667 0.87 2.0
H 0.16666667 -0.87 2.0
EOF_IN

cat<<EOF_CP2K > $TEST.cp2k
#!/bin/bash

cp quip_cp2k.xyz quip-pos-1_0.xyz
sed -e 's/pos/frc/' -e 's/\(Prop.*\)/\\1 E=42.0/' < quip-pos-1_0.xyz > quip-frc-1_0.xyz

EOF_CP2K

chmod +x $TEST.cp2k

cp $QUIP_ROOT/src/FilePot_drivers/cp2k_driver/cp2k_input.template $TEST.cp2k_input.template

$bindir/cp2k_driver $TEST.in.xyz $TEST.out.xyz Run_Type=MM cp2k_program=../$TEST.cp2k PSF_print=DRIVER_PRINT_AND_SAVE cp2k_template_file=$TEST.cp2k_input.template


cat<<EOF_OUT > $TEST.out.ref.xyz
6
Library=$TEST.all_res.CHARMM.lib energy=1142.8786362000001 Lattice="10.0000000000000      0.0000000000000      0.0000000000000      0.0000000000000     10.0000000000000      0.0000000000000      0.0000000000000      0.0000000000000     10.0000000000000" Properties=species:S:1:pos:R:3:Z:I:1:map_shift:I:3:n_neighb:I:1:travel:I:3:motif_atom_num:I:1:atom_type:S:1:atom_type_PDB:S:1:atom_res_name:S:1:atom_mol_name:S:1:atom_res_number:I:1:atom_subgroup_number:I:1:atom_res_type:I:1:atom_charge:R:1:mol_id:I:1:sort_index:I:1:force:R:3
H              0.8700000000000    -0.1666666670000    -2.0000000000000       1       0       0       0       1       0       0       0       3 HT        HT        TIP3      TIP3             1       0       1     0.4170000000000       1       2    44.7372115985426    -8.5703471516510  -102.8441647913703
O             -0.0000000000000     0.3333333330000    -2.0000000000000       8       0       0       0       2       0       0       0       1 OT        OT        TIP3      TIP3             1       0       1    -0.8340000000000       1       1    -0.0000000857035    17.1406940461916  -102.8441647913703
H             -0.8700000000000    -0.1666666670000    -2.0000000000000       1       0       0       0       1       0       0       0       2 HT        HT        TIP3      TIP3             1       0       1     0.4170000000000       1       3   -44.7372117699496    -8.5703471516510  -102.8441647913703
O             -0.3333333300000    -0.0000000000000     2.0000000000000       8       0       0       0       2       0       0       0       1 OT        OT        TIP3      TIP3             2       0       1    -0.8340000000000       2       4   -17.1406940461916     0.0000000857035   102.8441647913703
H              0.1666666700000     0.8700000000000     2.0000000000000       1       0       0       0       1       0       0       0       3 HT        HT        TIP3      TIP3             2       0       1     0.4170000000000       2       5     8.5703471516510    44.7372117699496   102.8441647913703
H              0.1666666700000    -0.8700000000000     2.0000000000000       1       0       0       0       1       0       0       0       2 HT        HT        TIP3      TIP3             2       0       1     0.4170000000000       2       6     8.5703471516510   -44.7372115985426   102.8441647913703
EOF_OUT

tail -6 $TEST.out.xyz | awk '{print $1" "$2" "$3" "$4" "$24" "$25" "$26}' > $TEST.out.xyz.pos_force
tail -6 $TEST.out.ref.xyz | awk '{print $1" "$2" "$3" "$4" "$24" "$25" "$26}' > $TEST.out.ref.xyz.pos_force

diff=diff; diffarg=-b
if which ndiff > /dev/null; then
  diff=ndiff
  diffarg=""
fi

if $diff $diffarg $TEST.out.xyz.pos_force $TEST.out.ref.xyz.pos_force; then
   echo "OK? T"
else
   echo "OK? F"
fi

rm -r $TEST.* cp2k_run_* cp2k_driver_in_log.xyz cp2k_output_log cp2k_input_log cp2k_force_file_log quip_rev_sort_index quip_cp2k.psf
