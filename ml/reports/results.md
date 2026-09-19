# Hasil perbandingan model

Dipilih berdasarkan macro-F1 validation. Terbaik: `ens[indobertweet+svc_wordchar_C0.1]`. Dideploy ke web: `svc_wordchar_C0.1`.

| Model | Fitur | Val macro-F1 | Test macro-F1 | Test macro-F1 tanpa geser bias | Test accuracy | F1 negatif | F1 netral | F1 positif | Detik latih |
|---|---|---|---|---|---|---|---|---|---|
| ens[indobertweet+svc_wordchar_C0.1] | transformer+wordchar | 0.6868 | 0.6906 | 0.6294 | 0.8343 | 0.894 | 0.313 | 0.865 | - |
| indobertweet | transformer | 0.6843 | 0.6921 | 0.6363 | 0.8304 | 0.891 | 0.323 | 0.862 | 894 |
| indobertweet_int8 | transformer | 0.6778 | 0.6837 | 0.6085 | 0.8228 | 0.887 | 0.310 | 0.854 | 894 |
| svc_wordchar_C0.1 | wordchar | 0.6649 | 0.6678 | 0.6122 | 0.8273 | 0.889 | 0.271 | 0.843 | 29.1 |
| ens[svc_word_C0.1+svc_word_C0.2] | word | 0.6644 | 0.6649 | 0.6093 | 0.8262 | 0.887 | 0.267 | 0.841 | - |
| svc_word_C0.1 | word | 0.6639 | 0.6657 | 0.6087 | 0.8216 | 0.886 | 0.273 | 0.839 | 20.7 |
| ens[svc_wordchar_C0.1+svc_wordchar_C0.05] | wordchar | 0.6639 | 0.6692 | 0.6094 | 0.8233 | 0.886 | 0.277 | 0.845 | - |
| svc_wordchar_C0.05 | wordchar | 0.6635 | 0.6662 | 0.6096 | 0.8293 | 0.889 | 0.265 | 0.844 | 18.7 |
| svc_word_C0.2 | word | 0.6632 | 0.6632 | 0.6144 | 0.8257 | 0.887 | 0.262 | 0.841 | 29.9 |
| svc_wordchar_C0.2 | wordchar | 0.6631 | 0.6650 | 0.6172 | 0.8214 | 0.885 | 0.268 | 0.842 | 61.4 |
| svc_word_C0.05 | word | 0.6616 | 0.6636 | 0.6054 | 0.8221 | 0.885 | 0.267 | 0.839 | 17.6 |
| svc_wordchar_C0.1_bal | wordchar | 0.6615 | 0.6667 | 0.6630 | 0.8079 | 0.875 | 0.285 | 0.840 | 53.5 |
| svc_wordnoslang_C0.1 | word_noslang | 0.6608 | 0.6661 | 0.6069 | 0.8212 | 0.884 | 0.275 | 0.839 | 35.2 |
| svc_wordnoslang_C0.2 | word_noslang | 0.6603 | 0.6648 | 0.6119 | 0.8215 | 0.884 | 0.271 | 0.839 | 46.4 |
| lr_wordchar_C2.0 | wordchar | 0.6594 | 0.6628 | 0.6285 | 0.8207 | 0.882 | 0.265 | 0.841 | 339.6 |
| svc_wordchar_C0.4 | wordchar | 0.6589 | 0.6582 | 0.6204 | 0.8177 | 0.881 | 0.255 | 0.839 | 67.5 |
| lgbm_word_chi2k30000 | word | 0.6587 | 0.6579 | 0.6198 | 0.8054 | 0.870 | 0.271 | 0.833 | 1068.1 |
| lr_word_C2.0 | word | 0.6586 | 0.6614 | 0.6232 | 0.8179 | 0.880 | 0.267 | 0.837 | 126.5 |
| svc_word_C0.5 | word | 0.6555 | 0.6551 | 0.6182 | 0.8158 | 0.879 | 0.249 | 0.837 | 39.9 |
| lr_word_C8.0 | word | 0.6475 | 0.6483 | 0.6291 | 0.8026 | 0.869 | 0.250 | 0.827 | 134.7 |
| mnb_word_a0.1 | word | 0.6470 | 0.6510 | 0.6117 | 0.7958 | 0.863 | 0.264 | 0.826 | 0.2 |
| lr_wordchar_C8.0 | wordchar | 0.6441 | 0.6466 | 0.6313 | 0.7951 | 0.864 | 0.251 | 0.825 | 974.4 |
| sgdhuber_wordchar | wordchar | 0.6438 | 0.6447 | 0.6280 | 0.8236 | 0.880 | 0.221 | 0.833 | 96.3 |
| ridge_wordchar_a3.0 | wordchar | 0.6432 | 0.6463 | 0.5796 | 0.7971 | 0.875 | 0.227 | 0.837 | 108.7 |
| ridge_wordchar_a1.0 | wordchar | 0.6391 | 0.6403 | 0.5768 | 0.7960 | 0.871 | 0.212 | 0.838 | 199.6 |
| ridge_word_a1.0 | word | 0.6360 | 0.6370 | 0.5769 | 0.8036 | 0.872 | 0.198 | 0.841 | 7.6 |
| cnb_word_a0.1 | word | 0.6323 | 0.6356 | 0.6206 | 0.7832 | 0.868 | 0.232 | 0.807 | 0.2 |
| cnb_word_a0.3 | word | 0.6305 | 0.6341 | 0.6177 | 0.7934 | 0.867 | 0.221 | 0.814 | 0.2 |
| cnb_word_a1.0 | word | 0.6245 | 0.6275 | 0.6032 | 0.7863 | 0.863 | 0.207 | 0.812 | 0.2 |
| dummy_majority | word | 0.2459 | 0.2467 | 0.2467 | 0.5875 | 0.740 | 0.000 | 0.000 | 0.0 |

## Model deploy: analisis tambahan (test)
```json
{
  "test_weighted_by_frequency": {
    "macro_f1": 0.6903,
    "accuracy": 0.8592
  },
  "test_by_app": {
    "BMKG": 0.6434,
    "JMO": 0.6863,
    "KAI": 0.6559,
    "mobileJKN": 0.6609,
    "pertamina": 0.6532,
    "satusehat": 0.6437
  },
  "test_agree_1": 0.6675,
  "polarity_flip_rate": 0.0662,
  "binary_neg_pos": {
    "accuracy": 0.9108,
    "macro_f1": 0.9021
  },
  "label_noise_ceiling": {
    "keys_seen_2plus": 12988,
    "rows_in_those_keys": 268270,
    "oracle_accuracy_on_duplicated_rows": 0.9453,
    "oracle_macro_f1_on_duplicated_rows": 0.6701,
    "neutral_rows_whose_text_majority_is_not_neutral": 0.9236,
    "example_mixed": {
      "mantap": {
        "negative": 295,
        "neutral": 324,
        "positive": 19155
      },
      "bagus": {
        "negative": 483,
        "neutral": 798,
        "positive": 21023
      },
      "ok": {
        "negative": 529,
        "neutral": 895,
        "positive": 25600
      },
      "lumayan": {
        "negative": 81,
        "neutral": 302,
        "positive": 631
      },
      "aplikasi sangat membantu": {
        "negative": 1,
        "neutral": 2,
        "positive": 276
      }
    }
  }
}
```