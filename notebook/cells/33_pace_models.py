#> ### 3.3 Feature engineering and pace models
#> Ridge with per-compound tyre age and age² terms, track temperature and driver dummies, against a Random Forest (5-fold CV). Ridge is kept: tree models go flat beyond the tyre ages they have seen, which would make long stints look free.
COMPOUNDS = sorted(clean['Compound'].unique())

def make_features(df, columns=None):
    X = pd.DataFrame(index=df.index)
    for c in COMPOUNDS:
        is_c = (df['Compound'] == c).astype(float)
        X[f'is_{c}']   = is_c
        X[f'age_{c}']  = is_c * df['TyreLife']
        X[f'age2_{c}'] = is_c * df['TyreLife'] ** 2
    X['TrackTemp'] = df['TrackTemp']
    X = pd.concat([X, pd.get_dummies(df['Driver'], prefix='drv', dtype=float)], axis=1)
    if columns is not None:
        X = X.reindex(columns=columns, fill_value=0.0)
    return X

X = make_features(clean)
y = clean['FuelCorrS']
FEATURES = X.columns

models = {
    'Ridge':        make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
    'RandomForest': RandomForestRegressor(n_estimators=300, min_samples_leaf=5,
                                          random_state=SEED, n_jobs=-1),
}
cv = KFold(n_splits=5, shuffle=True, random_state=SEED)
cv_pred = {}
for name, m in models.items():
    cv_pred[name] = cross_val_predict(m, X, y, cv=cv)
    print(f'{name:13s} MAE = {mean_absolute_error(y, cv_pred[name]):.3f} s'
          f'   R2 = {r2_score(y, cv_pred[name]):.3f}')

pace_model = models['Ridge'].fit(X, y)
LAP_NOISE  = np.std(y - cv_pred['Ridge'])
print(f'Lap-to-lap noise: {LAP_NOISE:.2f} s')
