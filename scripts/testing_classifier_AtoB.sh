#! env/bin/python3
GPU=$1
export CUDA_DEVICE_ORDER="PCI_BUS_ID"
export CUDA_VISIBLE_DEVICES=${GPU}
export PYTHONUNBUFFERED=1
if [ -z "$GPU" ]; then
  echo "Starting training on CPU."
else
  echo "Starting training on GPU ${GPU}."
fi
python3 -u main.py --dataset_dir='/home/013829790/Dataset2' \
  --dataset_A_dir='bhairavi' --dataset_B_dir='shanmukhpriya' \
  --checkpoint_dir='/home/013829790/output/checkpoint' \
  --sample_dir='/home/013829790/output/samples' \
  --test_dir='/home/013829790/output/test' \
  --log_dir='/home/013829790/output/log' \
  --type='classifier' --model='base' --sigma_d=0 -- sigma_c=0 --phase='test' \
  --which_direction="AtoB"

echo "Done."
# command : bash testing_classifier_AtoB.sh 0 > testing_classifier_AtoB.out 2> testing_classifier_AtoB.err
