import securexgboost as xgb
import os

DIR = os.path.dirname(os.path.realpath(__file__))
HOME_DIR = DIR + "/../../../"

train_enc_1 = HOME_DIR + "demo/python/multiclient/train1.enc"
test_enc_1 = HOME_DIR + "demo/python/multiclient/test1.enc"

print("Creating enclave")
enclave = xgb.Enclave(HOME_DIR + "build/enclave/xgboost_enclave.signed", log_verbosity=0)

# Remote Attestation
print("Remote attestation")
enclave.attest(verify=False)

username1 = "user1"
train_enc_1 = HOME_DIR + "demo/python/multiclient/train1.enc"
test_enc_1 = HOME_DIR + "demo/python/multiclient/test1.enc"

KEY_FILE_1 = HOME_DIR + "demo/python/multiclient/key1.txt"
PRIVATE_KEY_FILE_1 = HOME_DIR + "demo/data/userkeys/private_user_1.pem"
CERT_FILE_1 = DIR + "/../../data/usercrts/user1.crt"

xgb.init_user(username1, KEY_FILE_1, PRIVATE_KEY_FILE_1, CERT_FILE_1)
print("Send private key to enclave")
enclave.add_key()

username2 = "user2"
train_enc_2 = HOME_DIR + "demo/python/multiclient/train2.enc"
test_enc_2 = HOME_DIR + "demo/python/multiclient/test2.enc"

KEY_FILE_2 = HOME_DIR + "demo/python/multiclient/key2.txt"
PRIVATE_KEY_FILE_2 = HOME_DIR + "demo/data/userkeys/private_user_2.pem"
CERT_FILE_2 = DIR + "/../../data/usercrts/user2.crt"

xgb.init_user(username2, KEY_FILE_2, PRIVATE_KEY_FILE_2, CERT_FILE_2)

print("Send private key to enclave")
enclave.add_key()

rabit_args = {
        "DMLC_NUM_WORKER": os.environ.get("DMLC_NUM_WORKER"),
        "DMLC_NUM_SERVER": os.environ.get("DMLC_NUM_SERVER"),
        "DMLC_TRACKER_URI": os.environ.get("DMLC_TRACKER_URI"),
        "DMLC_TRACKER_PORT": os.environ.get("DMLC_TRACKER_PORT"),
        "DMLC_ROLE": os.environ.get("DMLC_ROLE"),
        "DMLC_NODE_HOST": os.environ.get("DMLC_NODE_HOST")
}

rargs = [str.encode(str(k) + "=" + str(v)) for k, v in rabit_args.items()]

xgb.rabit.init(rargs)

print("Creating training matrix from encrypted file")
dtrain = xgb.DMatrix({username1: train_enc_1, username2: train_enc_2}) 

#  print("Creating test matrix from encrypted file")
dtest = xgb.DMatrix({username1: test_enc_1})

print("Beginning Training")

# Set training parameters
params = {
        "tree_method": "hist",
        "n_gpus": "0",
        "objective": "binary:logistic",
        "min_child_weight": "1",
        "gamma": "0.1",
        "max_depth": "3",
        "verbosity": "1" 
}

# Train and evaluate
num_rounds = 3 
booster = xgb.train(params, dtrain, num_rounds, evals=[(dtrain, "train"), (dtest, "test")])
#  booster.save_model(DIR + "/demo_model.model")

# Get encrypted predictions
print("\n\nModel Predictions: ")
predictions, num_preds = booster.predict(dtest, decrypt=False)

# Decrypt predictions
print(booster.decrypt_predictions(predictions, num_preds)[0][:20])

xgb.rabit.finalize()
